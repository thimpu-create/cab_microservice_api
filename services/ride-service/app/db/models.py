"""
Ride domain models. Ride-service owns ride records and business rules.
"""
import enum
import uuid
from sqlalchemy import Column, String, Float, Integer, Text, DateTime, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.db.base import Base


class RideStatusEnum(str, enum.Enum):
    pending = "pending"
    assigned = "assigned"
    in_progress = "in_progress"
    completed = "completed"
    cancelled = "cancelled"
    expired = "expired"
    rejected = "rejected"


class Ride(Base):
    __tablename__ = "rides"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    request_id = Column(String(255), unique=True, nullable=False, index=True)

    passenger_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    driver_id = Column(UUID(as_uuid=True), nullable=True, index=True)

    pickup_lat = Column(Float, nullable=False)
    pickup_lon = Column(Float, nullable=False)
    pickup_address = Column(Text, nullable=True)
    dropoff_lat = Column(Float, nullable=True)
    dropoff_lon = Column(Float, nullable=True)
    dropoff_address = Column(Text, nullable=True)

    vehicle_type = Column(String(20), nullable=True)  # bike, car, auto, premium_car
    city_code = Column(String(10), nullable=True)

    status = Column(SQLEnum(RideStatusEnum), nullable=False, default=RideStatusEnum.pending)
    distance_km = Column(Float, nullable=True)
    duration_minutes = Column(Integer, nullable=True)
    fare_amount = Column(Float, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    assigned_at = Column(DateTime(timezone=True), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    cancelled_at = Column(DateTime(timezone=True), nullable=True)
    cancelled_by = Column(String(50), nullable=True)
    cancellation_reason = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
