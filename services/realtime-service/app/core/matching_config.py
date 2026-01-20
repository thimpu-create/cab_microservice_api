"""
Configuration loader for matching algorithm weights.
Allows dynamic configuration from environment variables or config file.
"""
from app.core.config import settings
from app.core.matching_algorithm import MatchingWeights


def get_matching_weights() -> MatchingWeights:
    """
    Get matching weights from configuration.
    Can be extended to load from database or external config service.
    """
    weights = MatchingWeights()
    
    # Override with config values if available
    if hasattr(settings, 'MATCHING_DISTANCE_WEIGHT'):
        weights.DISTANCE_WEIGHT = settings.MATCHING_DISTANCE_WEIGHT
    if hasattr(settings, 'MATCHING_RATING_WEIGHT'):
        weights.RATING_WEIGHT = settings.MATCHING_RATING_WEIGHT
    if hasattr(settings, 'MATCHING_VEHICLE_TYPE_WEIGHT'):
        weights.VEHICLE_TYPE_WEIGHT = settings.MATCHING_VEHICLE_TYPE_WEIGHT
    if hasattr(settings, 'MATCHING_VERIFICATION_WEIGHT'):
        weights.VERIFICATION_WEIGHT = settings.MATCHING_VERIFICATION_WEIGHT
    if hasattr(settings, 'MATCHING_MIN_RATING_THRESHOLD'):
        weights.MIN_RATING_THRESHOLD = settings.MATCHING_MIN_RATING_THRESHOLD
    if hasattr(settings, 'MATCHING_MAX_DISTANCE_KM'):
        weights.MAX_DISTANCE_KM = settings.MATCHING_MAX_DISTANCE_KM
    
    # Normalize weights to sum to 1.0
    total = (
        weights.DISTANCE_WEIGHT +
        weights.RATING_WEIGHT +
        weights.VEHICLE_TYPE_WEIGHT +
        weights.VERIFICATION_WEIGHT
    )
    
    if total > 0:
        weights.DISTANCE_WEIGHT /= total
        weights.RATING_WEIGHT /= total
        weights.VEHICLE_TYPE_WEIGHT /= total
        weights.VERIFICATION_WEIGHT /= total
    
    return weights
