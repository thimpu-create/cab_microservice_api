import uuid
from sqlalchemy import (
    Column, String, Boolean, DateTime, Enum, Text, Integer, Float, ForeignKey
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .base import Base
import enum


class DriverStatus(enum.Enum):
    active = "active"
    inactive = "inactive"
    suspended = "suspended"
    pending_verification = "pending_verification"


class VehicleType(enum.Enum):
    """Vehicle types - extensible enum for future additions."""
    bike = "bike"
    car = "car"
    auto = "auto"  # Auto-rickshaw
    premium_car = "premium_car"


class Driver(Base):
    __tablename__ = "drivers"

    # ---- Identity ----
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)  # Links to auth-service users table
    company_id = Column(UUID(as_uuid=True), nullable=True, index=True)  # Links to company-service cab_companies table
    # null company_id means independent driver

    # ---- Personal Information ----
    license_number = Column(String(100), nullable=True)
    license_expiry_date = Column(DateTime, nullable=True)
    license_state_province = Column(String(100), nullable=True)

    # ---- Vehicle Information ----
    vehicle_type = Column(Enum(VehicleType), nullable=True)  # bike, car, auto, premium_car
    vehicle_make = Column(String(100), nullable=True)
    vehicle_model = Column(String(100), nullable=True)
    vehicle_year = Column(Integer, nullable=True)
    vehicle_color = Column(String(50), nullable=True)
    vehicle_plate_number = Column(String(50), nullable=True)

    # ---- Status & Verification ----
    status = Column(Enum(DriverStatus), default=DriverStatus.pending_verification)
    is_verified = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)

    # ---- Additional Info ----
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # ---- Relationships ----
    ratings = relationship("DriverRating", back_populates="driver", cascade="all, delete-orphan")


class DriverRating(Base):
    """Driver rating model - stores ratings given by passengers after rides."""
    __tablename__ = "driver_ratings"

    # ---- Primary Key ----
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # ---- Foreign Keys ----
    driver_id = Column(UUID(as_uuid=True), ForeignKey("drivers.id", ondelete="CASCADE"), nullable=False, index=True)
    passenger_id = Column(UUID(as_uuid=True), nullable=False, index=True)  # Links to auth-service users.uuid
    ride_id = Column(UUID(as_uuid=True), nullable=True, index=True)  # Links to realtime-service rides.id (optional)
    
    # ---- Rating Details ----
    rating = Column(Float, nullable=False)  # Rating from 1.0 to 5.0
    comment = Column(Text, nullable=True)  # Optional comment from passenger
    
    # ---- Rating Categories (optional, for detailed feedback) ----
    punctuality_rating = Column(Float, nullable=True)  # 1.0 to 5.0
    driving_rating = Column(Float, nullable=True)  # 1.0 to 5.0
    vehicle_condition_rating = Column(Float, nullable=True)  # 1.0 to 5.0
    communication_rating = Column(Float, nullable=True)  # 1.0 to 5.0
    
    # ---- Metadata ----
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # ---- Relationships ----
    driver = relationship("Driver", back_populates="ratings")
