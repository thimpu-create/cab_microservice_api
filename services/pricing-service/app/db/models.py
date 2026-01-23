import uuid
from sqlalchemy import Column, String, Float, DateTime, Boolean, ForeignKey, Integer, Text, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.db.base import Base


class VehicleType(str, enum.Enum):
    """Vehicle types - must match driver-service enum."""
    bike = "bike"
    car = "car"
    auto = "auto"
    premium_car = "premium_car"


class PricingProfile(Base):
    """Base pricing rules per vehicle type per city."""
    __tablename__ = "pricing_profiles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Location
    city_code = Column(String(10), nullable=False, index=True)  # e.g., "MUM", "DEL", "BLR"
    state_code = Column(String(10), nullable=True, index=True)  # Optional state code
    
    # Vehicle type
    vehicle_type = Column(SQLEnum(VehicleType), nullable=False, index=True)
    
    # Pricing components
    base_fare = Column(Float, nullable=False)  # Fixed charge per ride
    per_km_rate = Column(Float, nullable=False)  # Cost per kilometer
    per_minute_rate = Column(Float, nullable=False)  # Cost per minute
    minimum_fare = Column(Float, nullable=False)  # Minimum fare
    
    # Status
    is_active = Column(Boolean, nullable=False, default=True)
    
    # Time-based pricing (optional)
    effective_from = Column(DateTime(timezone=True), nullable=True)
    effective_to = Column(DateTime(timezone=True), nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class PeakHours(Base):
    """Peak hours definition per city with multiplier."""
    __tablename__ = "peak_hours"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Location
    city_code = Column(String(10), nullable=False, index=True)
    
    # Time definition
    day_of_week = Column(Integer, nullable=True)  # 0=Monday, 6=Sunday, NULL=all days
    start_time = Column(String(5), nullable=False)  # HH:MM format (24-hour)
    end_time = Column(String(5), nullable=False)  # HH:MM format (24-hour)
    
    # Multiplier
    multiplier = Column(Float, nullable=False, default=1.2)  # e.g., 1.2 = 20% surcharge
    
    # Status
    is_active = Column(Boolean, nullable=False, default=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class SurgeConfig(Base):
    """Surge calculation parameters per vehicle type."""
    __tablename__ = "surge_configs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Vehicle type
    vehicle_type = Column(SQLEnum(VehicleType), nullable=False, unique=True, index=True)
    
    # Surge parameters
    base_demand_threshold = Column(Float, nullable=False, default=1.5)  # Demand/supply ratio to start surge
    max_surge_multiplier = Column(Float, nullable=False, default=3.0)  # Maximum surge (e.g., 3.0x)
    surge_increment = Column(Float, nullable=False, default=0.2)  # Surge increment per demand unit
    
    # Status
    is_active = Column(Boolean, nullable=False, default=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class RegulatoryCap(Base):
    """Maximum fare caps per city/state (regulatory compliance)."""
    __tablename__ = "regulatory_caps"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Location
    city_code = Column(String(10), nullable=True, index=True)  # NULL = applies to all cities
    state_code = Column(String(10), nullable=True, index=True)  # NULL = applies to all states
    
    # Vehicle type
    vehicle_type = Column(SQLEnum(VehicleType), nullable=True)  # NULL = applies to all vehicle types
    
    # Cap
    max_fare_amount = Column(Float, nullable=False)
    
    # Time-based
    effective_from = Column(DateTime(timezone=True), nullable=True)
    effective_to = Column(DateTime(timezone=True), nullable=True)
    
    # Status
    is_active = Column(Boolean, nullable=False, default=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class PricingCalculation(Base):
    """Audit log of all pricing calculations."""
    __tablename__ = "pricing_calculations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Request info
    request_id = Column(String(100), nullable=True, index=True)  # Ride request ID
    user_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    
    # Location
    city_code = Column(String(10), nullable=True, index=True)
    pickup_lat = Column(Float, nullable=True)
    pickup_lon = Column(Float, nullable=True)
    dropoff_lat = Column(Float, nullable=True)
    dropoff_lon = Column(Float, nullable=True)
    
    # Ride details
    vehicle_type = Column(SQLEnum(VehicleType), nullable=False)
    distance_km = Column(Float, nullable=False)
    duration_minutes = Column(Float, nullable=False)
    
    # Pricing breakdown
    base_fare = Column(Float, nullable=False)
    distance_cost = Column(Float, nullable=False)
    time_cost = Column(Float, nullable=False)
    subtotal = Column(Float, nullable=False)
    
    # Multipliers
    peak_multiplier = Column(Float, nullable=False, default=1.0)
    surge_multiplier = Column(Float, nullable=False, default=1.0)
    
    # Final fare
    final_fare = Column(Float, nullable=False)
    
    # Constraints applied
    minimum_fare_applied = Column(Boolean, nullable=False, default=False)
    regulatory_cap_applied = Column(Boolean, nullable=False, default=False)
    
    # Metadata
    calculated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
