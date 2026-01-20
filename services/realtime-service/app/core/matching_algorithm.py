"""
Advanced ride matching algorithm with configurable scoring.
Supports driver ratings, vehicle type matching, and distance optimization.
"""
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass
from enum import Enum

from app.core.driver_info_client import driver_info_client


class VehicleType(str, Enum):
    """Vehicle types - matches driver service enum."""
    BIKE = "bike"
    CAR = "car"
    AUTO = "auto"
    PREMIUM_CAR = "premium_car"


@dataclass
class DriverMatch:
    """Represents a driver match with scoring details."""
    driver_id: str
    distance_km: float
    score: float
    vehicle_type: Optional[str] = None
    average_rating: float = 0.0
    total_ratings: int = 0
    is_verified: bool = False
    score_breakdown: Optional[Dict[str, float]] = None


class MatchingWeights:
    """
    Configurable weights for matching algorithm.
    Can be adjusted via environment variables or config in the future.
    """
    # Distance weight (closer = higher score, so we use inverse)
    DISTANCE_WEIGHT = 0.4  # 40% weight on distance
    
    # Rating weight (higher = higher score)
    RATING_WEIGHT = 0.3  # 30% weight on rating
    
    # Vehicle type match weight
    VEHICLE_TYPE_WEIGHT = 0.2  # 20% weight on vehicle type match
    
    # Verification/status weight
    VERIFICATION_WEIGHT = 0.1  # 10% weight on verification status
    
    # Minimum rating threshold (drivers below this are deprioritized)
    MIN_RATING_THRESHOLD = 3.0
    
    # Maximum distance for matching (km)
    MAX_DISTANCE_KM = 10.0


class MatchingAlgorithm:
    """
    Advanced matching algorithm with weighted scoring.
    Configurable and extensible for future enhancements.
    """
    
    def __init__(self, weights: Optional[MatchingWeights] = None):
        self.weights = weights or MatchingWeights()
    
    def normalize_distance_score(self, distance_km: float, max_distance: float) -> float:
        """
        Normalize distance to a score (0-1).
        Closer drivers get higher scores.
        """
        if distance_km <= 0:
            return 1.0
        
        if distance_km >= max_distance:
            return 0.0
        
        # Inverse relationship: closer = higher score
        # Using exponential decay for better distribution
        normalized = 1.0 - (distance_km / max_distance)
        return max(0.0, normalized ** 0.5)  # Square root for smoother curve
    
    def normalize_rating_score(self, rating: float, min_rating: float = 1.0, max_rating: float = 5.0) -> float:
        """
        Normalize rating to a score (0-1).
        Higher ratings get higher scores.
        """
        if rating < min_rating:
            return 0.0
        
        if rating >= max_rating:
            return 1.0
        
        # Linear normalization
        return (rating - min_rating) / (max_rating - min_rating)
    
    def calculate_vehicle_type_score(
        self,
        driver_vehicle_type: Optional[str],
        requested_vehicle_type: Optional[str]
    ) -> float:
        """
        Calculate vehicle type match score.
        Returns 1.0 for exact match, 0.0 for no match, 0.5 for compatible types.
        """
        if not requested_vehicle_type:
            # No preference = all types get same score
            return 0.5
        
        if not driver_vehicle_type:
            # Driver has no vehicle type = lower score
            return 0.2
        
        # Exact match
        if driver_vehicle_type.lower() == requested_vehicle_type.lower():
            return 1.0
        
        # Compatible types (can be extended in future)
        compatible_groups = {
            "car": ["car", "premium_car"],
            "premium_car": ["premium_car", "car"],
        }
        
        if requested_vehicle_type.lower() in compatible_groups:
            if driver_vehicle_type.lower() in compatible_groups[requested_vehicle_type.lower()]:
                return 0.7  # Partial match
        
        # No match
        return 0.0
    
    def calculate_verification_score(self, is_verified: bool, is_active: bool) -> float:
        """Calculate score based on verification and active status."""
        if is_verified and is_active:
            return 1.0
        elif is_verified:
            return 0.7
        elif is_active:
            return 0.5
        else:
            return 0.2
    
    async def score_drivers(
        self,
        drivers_with_distance: List[Tuple[str, float]],  # [(driver_id, distance_km), ...]
        requested_vehicle_type: Optional[str] = None,
        min_rating: Optional[float] = None
    ) -> List[DriverMatch]:
        """
        Score and rank drivers based on multiple factors.
        
        Args:
            drivers_with_distance: List of (driver_id, distance_km) tuples
            requested_vehicle_type: Preferred vehicle type (bike, car, auto, premium_car)
            min_rating: Minimum rating threshold (optional)
        
        Returns:
            List of DriverMatch objects sorted by score (highest first)
        """
        if not drivers_with_distance:
            return []
        
        # Fetch driver information in batch
        driver_ids = [driver_id for driver_id, _ in drivers_with_distance]
        driver_info_dict = await driver_info_client.get_drivers_batch_info(driver_ids)
        
        # Calculate scores for each driver
        matches = []
        min_rating_threshold = min_rating or self.weights.MIN_RATING_THRESHOLD
        
        for driver_id, distance_km in drivers_with_distance:
            # Skip if beyond max distance
            if distance_km > self.weights.MAX_DISTANCE_KM:
                continue
            
            driver_info = driver_info_dict.get(driver_id, {})
            
            # Get driver attributes
            vehicle_type = driver_info.get("vehicle_type")
            average_rating = driver_info.get("average_rating", 0.0)
            total_ratings = driver_info.get("total_ratings", 0)
            is_verified = driver_info.get("is_verified", False)
            is_active = driver_info.get("is_active", False)
            
            # Skip drivers below minimum rating (but don't exclude completely)
            if average_rating > 0 and average_rating < min_rating_threshold:
                # Deprioritize but don't exclude
                rating_penalty = 0.5
            else:
                rating_penalty = 1.0
            
            # Calculate component scores
            distance_score = self.normalize_distance_score(distance_km, self.weights.MAX_DISTANCE_KM)
            rating_score = self.normalize_rating_score(average_rating) * rating_penalty
            vehicle_type_score = self.calculate_vehicle_type_score(vehicle_type, requested_vehicle_type)
            verification_score = self.calculate_verification_score(is_verified, is_active)
            
            # Calculate weighted composite score
            composite_score = (
                distance_score * self.weights.DISTANCE_WEIGHT +
                rating_score * self.weights.RATING_WEIGHT +
                vehicle_type_score * self.weights.VEHICLE_TYPE_WEIGHT +
                verification_score * self.weights.VERIFICATION_WEIGHT
            )
            
            # Store score breakdown for debugging/transparency
            score_breakdown = {
                "distance_score": round(distance_score, 3),
                "rating_score": round(rating_score, 3),
                "vehicle_type_score": round(vehicle_type_score, 3),
                "verification_score": round(verification_score, 3),
            }
            
            matches.append(DriverMatch(
                driver_id=driver_id,
                distance_km=distance_km,
                score=composite_score,
                vehicle_type=vehicle_type,
                average_rating=average_rating,
                total_ratings=total_ratings,
                is_verified=is_verified,
                score_breakdown=score_breakdown
            ))
        
        # Sort by score (highest first)
        matches.sort(key=lambda x: x.score, reverse=True)
        
        return matches
    
    def update_weights(
        self,
        distance_weight: Optional[float] = None,
        rating_weight: Optional[float] = None,
        vehicle_type_weight: Optional[float] = None,
        verification_weight: Optional[float] = None
    ):
        """
        Update matching weights dynamically.
        Useful for A/B testing or configuration changes.
        """
        if distance_weight is not None:
            self.weights.DISTANCE_WEIGHT = distance_weight
        if rating_weight is not None:
            self.weights.RATING_WEIGHT = rating_weight
        if vehicle_type_weight is not None:
            self.weights.VEHICLE_TYPE_WEIGHT = vehicle_type_weight
        if verification_weight is not None:
            self.weights.VERIFICATION_WEIGHT = verification_weight
        
        # Normalize weights to sum to 1.0
        total = (
            self.weights.DISTANCE_WEIGHT +
            self.weights.RATING_WEIGHT +
            self.weights.VEHICLE_TYPE_WEIGHT +
            self.weights.VERIFICATION_WEIGHT
        )
        
        if total > 0:
            self.weights.DISTANCE_WEIGHT /= total
            self.weights.RATING_WEIGHT /= total
            self.weights.VEHICLE_TYPE_WEIGHT /= total
            self.weights.VERIFICATION_WEIGHT /= total


# Global matching algorithm instance (will be initialized with config)
matching_algorithm = None


def initialize_matching_algorithm():
    """Initialize matching algorithm with configuration."""
    global matching_algorithm
    from app.core.matching_config import get_matching_weights
    weights = get_matching_weights()
    matching_algorithm = MatchingAlgorithm(weights)
    return matching_algorithm


# Initialize on import
matching_algorithm = initialize_matching_algorithm()
