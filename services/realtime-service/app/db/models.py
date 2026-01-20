import uuid
from sqlalchemy import (
    Column, String, Boolean, DateTime, Enum, Text, Float, Integer
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from .base import Base
import enum


class RideStatus(enum.Enum):
    """Ride status enum matching the RideManager statuses."""
    pending = "pending"
    assigned = "assigned"
    in_progress = "in_progress"
    completed = "completed"
    cancelled = "cancelled"
    expired = "expired"
    rejected = "rejected"


class Ride(Base):
    """Ride model for persisting ride history."""
    __tablename__ = "rides"

    # ---- Primary Key ----
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    request_id = Column(String(255), unique=True, nullable=False, index=True)  # Original request ID from Redis

    # ---- Participants ----
    passenger_id = Column(UUID(as_uuid=True), nullable=False, index=True)  # Links to auth-service users.uuid
    driver_id = Column(UUID(as_uuid=True), nullable=True, index=True)  # Links to driver-service drivers.id

    # ---- Location Information ----
    pickup_lat = Column(Float, nullable=False)
    pickup_lon = Column(Float, nullable=False)
    pickup_address = Column(Text, nullable=True)
    
    dropoff_lat = Column(Float, nullable=True)
    dropoff_lon = Column(Float, nullable=True)
    dropoff_address = Column(Text, nullable=True)

    # ---- Ride Details ----
    status = Column(Enum(RideStatus), nullable=False, default=RideStatus.pending)
    distance_km = Column(Float, nullable=True)  # Total distance traveled
    duration_minutes = Column(Integer, nullable=True)  # Total duration in minutes
    fare_amount = Column(Float, nullable=True)  # Fare amount (if integrated with pricing service)

    # ---- Timestamps ----
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    assigned_at = Column(DateTime(timezone=True), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    cancelled_at = Column(DateTime(timezone=True), nullable=True)

    # ---- Cancellation Info ----
    cancelled_by = Column(String(50), nullable=True)  # "passenger" or "driver"
    cancellation_reason = Column(Text, nullable=True)

    # ---- Additional Info ----
    notes = Column(Text, nullable=True)

    # ---- Metadata ----
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
