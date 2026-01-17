import uuid
from sqlalchemy import (
    Column, String, Boolean, DateTime, Enum, Text, Integer
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from .base import Base
import enum


class DriverStatus(enum.Enum):
    active = "active"
    inactive = "inactive"
    suspended = "suspended"
    pending_verification = "pending_verification"


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
