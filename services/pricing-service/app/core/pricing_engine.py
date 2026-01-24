"""
Core pricing engine for calculating ride fares.
"""
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from app.db.models import (
    PricingProfile, PeakHours, SurgeConfig, RegulatoryCap,
    VehicleType
)
from app.core.redis_client import calculate_demand_supply_ratio
from app.core.utils import calculate_distance, is_peak_hours
from app.core.driver_info_client import get_driver_company_id
from app.core.config import settings
from uuid import UUID


class PricingEngine:
    """Core pricing engine for fare calculation."""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def calculate_fare(
        self,
        pickup_lat: float,
        pickup_lon: float,
        dropoff_lat: float,
        dropoff_lon: float,
        vehicle_type: VehicleType,
        city_code: str,
        driver_id: Optional[UUID] = None,
        company_id: Optional[UUID] = None,
        estimated_distance_km: Optional[float] = None,
        estimated_duration_minutes: Optional[float] = None,
        request_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Calculate fare for a ride.
        
        Args:
            driver_id: Driver ID (will fetch company_id if not provided)
            company_id: Company ID (NULL = independent driver, NOT NULL = company driver)
        
        Returns detailed breakdown including all components.
        """
        # Get company_id if driver_id provided
        if driver_id and not company_id:
            company_id = await get_driver_company_id(driver_id)
        
        # Calculate distance if not provided
        if estimated_distance_km is None:
            estimated_distance_km = calculate_distance(
                pickup_lat, pickup_lon, dropoff_lat, dropoff_lon
            )
        
        # Estimate duration if not provided (assume 30 km/h average speed)
        if estimated_duration_minutes is None:
            estimated_duration_minutes = (estimated_distance_km / 30.0) * 60
        
        # Get pricing profile (company_id = NULL for platform, NOT NULL for company)
        pricing_profile = self._get_pricing_profile(vehicle_type, city_code, company_id)
        if not pricing_profile:
            pricing_type = "platform" if company_id is None else "company"
            raise ValueError(f"No {pricing_type} pricing profile found for {vehicle_type.value} in {city_code}")
        
        # Calculate base components
        base_fare = pricing_profile.base_fare
        distance_cost = estimated_distance_km * pricing_profile.per_km_rate
        time_cost = estimated_duration_minutes * pricing_profile.per_minute_rate
        
        subtotal = base_fare + distance_cost + time_cost
        
        # Check peak hours (use company-specific or platform peak hours)
        current_time = datetime.now()
        peak_multiplier = self._get_peak_multiplier(city_code, current_time, company_id)
        peak_adjusted_subtotal = subtotal * peak_multiplier
        
        # Calculate surge (use company-specific or platform surge config)
        surge_multiplier = await self._calculate_surge(
            pickup_lat, pickup_lon, vehicle_type, company_id
        )
        surge_adjusted_subtotal = peak_adjusted_subtotal * surge_multiplier
        
        # Apply minimum fare
        minimum_fare = pricing_profile.minimum_fare
        if surge_adjusted_subtotal < minimum_fare:
            final_fare = minimum_fare
            minimum_fare_applied = True
        else:
            final_fare = surge_adjusted_subtotal
            minimum_fare_applied = False
        
        # Apply regulatory cap
        regulatory_cap = self._get_regulatory_cap(vehicle_type, city_code)
        regulatory_cap_applied = False
        if regulatory_cap and final_fare > regulatory_cap:
            final_fare = regulatory_cap
            regulatory_cap_applied = True
        
        # Calculate surcharges
        peak_surcharge = peak_adjusted_subtotal - subtotal
        surge_surcharge = surge_adjusted_subtotal - peak_adjusted_subtotal
        
        # Build response
        result = {
            "base_fare": round(base_fare, 2),
            "distance_cost": round(distance_cost, 2),
            "time_cost": round(time_cost, 2),
            "subtotal": round(subtotal, 2),
            "peak_multiplier": round(peak_multiplier, 2),
            "peak_adjusted_subtotal": round(peak_adjusted_subtotal, 2),
            "surge_multiplier": round(surge_multiplier, 2),
            "surge_adjusted_subtotal": round(surge_adjusted_subtotal, 2),
            "minimum_fare": round(minimum_fare, 2),
            "regulatory_cap": round(regulatory_cap, 2) if regulatory_cap else None,
            "final_fare": round(final_fare, 2),
            "currency": "INR",  # Can be made configurable
            "breakdown": {
                "base": round(base_fare, 2),
                "distance": round(distance_cost, 2),
                "time": round(time_cost, 2),
                "peak_surcharge": round(peak_surcharge, 2),
                "surge_surcharge": round(surge_surcharge, 2)
            },
            "metadata": {
                "distance_km": round(estimated_distance_km, 2),
                "duration_minutes": round(estimated_duration_minutes, 2),
                "vehicle_type": vehicle_type.value,
                "city_code": city_code,
                "company_id": str(company_id) if company_id else None,
                "pricing_type": "company" if company_id else "platform",
                "minimum_fare_applied": minimum_fare_applied,
                "regulatory_cap_applied": regulatory_cap_applied
            }
        }
        
        # Save calculation to audit log
        self._save_calculation(
            request_id=request_id,
            user_id=user_id,
            driver_id=driver_id,
            company_id=company_id,
            vehicle_type=vehicle_type,
            city_code=city_code,
            pickup_lat=pickup_lat,
            pickup_lon=pickup_lon,
            dropoff_lat=dropoff_lat,
            dropoff_lon=dropoff_lon,
            distance_km=estimated_distance_km,
            duration_minutes=estimated_duration_minutes,
            base_fare=base_fare,
            distance_cost=distance_cost,
            time_cost=time_cost,
            subtotal=subtotal,
            peak_multiplier=peak_multiplier,
            surge_multiplier=surge_multiplier,
            final_fare=final_fare,
            minimum_fare_applied=minimum_fare_applied,
            regulatory_cap_applied=regulatory_cap_applied
        )
        
        return result
    
    def _get_pricing_profile(self, vehicle_type: VehicleType, city_code: str, company_id: Optional[UUID] = None) -> Optional[PricingProfile]:
        """Get active pricing profile for vehicle type and city.
        company_id = NULL: Platform pricing (independent drivers)
        company_id = NOT NULL: Company pricing (company drivers)
        """
        from sqlalchemy import or_
        # Use proper NULL check
        if company_id is None:
            return self.db.query(PricingProfile).filter(
                PricingProfile.vehicle_type == vehicle_type,
                PricingProfile.city_code == city_code,
                PricingProfile.company_id.is_(None),  # Platform pricing
                PricingProfile.is_active == True
            ).first()
        else:
            return self.db.query(PricingProfile).filter(
                PricingProfile.vehicle_type == vehicle_type,
                PricingProfile.city_code == city_code,
                PricingProfile.company_id == company_id,  # Company pricing
                PricingProfile.is_active == True
            ).first()
    
    def _get_peak_multiplier(self, city_code: str, current_time: datetime, company_id: Optional[UUID] = None) -> float:
        """Get peak hours multiplier for current time.
        Uses company-specific peak hours if company_id provided, otherwise platform peak hours.
        """
        # Use proper NULL check
        if company_id is None:
            peak_hours = self.db.query(PeakHours).filter(
                PeakHours.city_code == city_code,
                PeakHours.company_id.is_(None),  # Platform peak hours
                PeakHours.is_active == True
            ).all()
        else:
            peak_hours = self.db.query(PeakHours).filter(
                PeakHours.city_code == city_code,
                PeakHours.company_id == company_id,  # Company peak hours
                PeakHours.is_active == True
            ).all()
        
        for peak in peak_hours:
            if is_peak_hours(current_time, peak.start_time, peak.end_time, peak.day_of_week):
                return peak.multiplier
        
        return 1.0  # No peak hours active
    
    async def _calculate_surge(
        self,
        area_lat: float,
        area_lon: float,
        vehicle_type: VehicleType,
        company_id: Optional[UUID] = None,
        radius_km: float = 10.0
    ) -> float:
        """
        Calculate surge multiplier based on demand/supply ratio.
        Uses company-specific surge config if company_id provided, otherwise platform surge config.
        """
        # Get surge config (company-specific or platform)
        surge_config = self.db.query(SurgeConfig).filter(
            SurgeConfig.vehicle_type == vehicle_type,
            SurgeConfig.company_id == company_id,  # Match company_id
            SurgeConfig.is_active == True
        ).first()
        
        if not surge_config:
            # Use defaults from config
            base_threshold = settings.DEFAULT_BASE_DEMAND_THRESHOLD
            max_surge = settings.DEFAULT_MAX_SURGE
            surge_increment = settings.DEFAULT_SURGE_INCREMENT
        else:
            base_threshold = surge_config.base_demand_threshold
            max_surge = surge_config.max_surge_multiplier
            surge_increment = surge_config.surge_increment
        
        # Calculate demand/supply ratio
        demand_supply_ratio = calculate_demand_supply_ratio(
            area_lat, area_lon, radius_km, vehicle_type.value
        )
        
        # Apply surge formula
        if demand_supply_ratio < base_threshold:
            surge_multiplier = 1.0
        else:
            excess_demand = demand_supply_ratio - base_threshold
            surge_multiplier = 1.0 + (excess_demand * surge_increment)
            surge_multiplier = min(surge_multiplier, max_surge)
        
        return surge_multiplier
    
    def _get_regulatory_cap(self, vehicle_type: VehicleType, city_code: str, company_id: Optional[UUID] = None) -> Optional[float]:
        """Get regulatory cap for vehicle type and city.
        Uses company-specific caps if company_id provided, otherwise platform caps.
        """
        # Try city-specific cap first
        if company_id is None:
            cap = self.db.query(RegulatoryCap).filter(
                RegulatoryCap.city_code == city_code,
                RegulatoryCap.vehicle_type == vehicle_type,
                RegulatoryCap.company_id.is_(None),  # Platform regulatory cap
                RegulatoryCap.is_active == True
            ).first()
        else:
            cap = self.db.query(RegulatoryCap).filter(
                RegulatoryCap.city_code == city_code,
                RegulatoryCap.vehicle_type == vehicle_type,
                RegulatoryCap.company_id == company_id,  # Company regulatory cap
                RegulatoryCap.is_active == True
            ).first()
        
        if cap:
            return cap.max_fare_amount
        
        # Try state-level cap (would need state_code)
        # For now, return None (no cap)
        return None
    
    def _save_calculation(
        self,
        request_id: Optional[str],
        user_id: Optional[str],
        driver_id: Optional[UUID],
        company_id: Optional[UUID],
        vehicle_type: VehicleType,
        city_code: str,
        pickup_lat: float,
        pickup_lon: float,
        dropoff_lat: float,
        dropoff_lon: float,
        distance_km: float,
        duration_minutes: float,
        base_fare: float,
        distance_cost: float,
        time_cost: float,
        subtotal: float,
        peak_multiplier: float,
        surge_multiplier: float,
        final_fare: float,
        minimum_fare_applied: bool,
        regulatory_cap_applied: bool
    ):
        """Save pricing calculation to audit log."""
        from app.db.models import PricingCalculation
        
        calculation = PricingCalculation(
            request_id=request_id,
            user_id=UUID(user_id) if user_id else None,
            driver_id=driver_id,
            company_id=company_id,
            city_code=city_code,
            pickup_lat=pickup_lat,
            pickup_lon=pickup_lon,
            dropoff_lat=dropoff_lat,
            dropoff_lon=dropoff_lon,
            vehicle_type=vehicle_type,
            distance_km=distance_km,
            duration_minutes=duration_minutes,
            base_fare=base_fare,
            distance_cost=distance_cost,
            time_cost=time_cost,
            subtotal=subtotal,
            peak_multiplier=peak_multiplier,
            surge_multiplier=surge_multiplier,
            final_fare=final_fare,
            minimum_fare_applied=minimum_fare_applied,
            regulatory_cap_applied=regulatory_cap_applied
        )
        
        self.db.add(calculation)
        self.db.commit()
