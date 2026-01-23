import uuid
from sqlalchemy import Column, String, Float, DateTime, Boolean, ForeignKey, Integer, Text, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.db.base import Base


class SOSStatus(str, enum.Enum):
    """Status of SOS request."""
    triggered = "triggered"
    active = "active"
    resolved = "resolved"
    cancelled = "cancelled"


class SOSRequest(Base):
    """SOS emergency request."""
    __tablename__ = "sos_requests"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Location (live location when triggered)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    address = Column(Text, nullable=True)  # Optional address string
    
    # Emergency number used
    emergency_number = Column(String(20), nullable=False, default="112")
    
    # Status
    status = Column(SQLEnum(SOSStatus), nullable=False, default=SOSStatus.triggered)
    
    # Timestamps
    triggered_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    
    # Additional info
    notes = Column(Text, nullable=True)
    
    # Relationships
    contacts_notified = relationship("SOSContactNotification", back_populates="sos_request", cascade="all, delete-orphan")


class EmergencyContact(Base):
    """User's emergency contacts (max 5 per user)."""
    __tablename__ = "emergency_contacts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Contact info
    name = Column(String(200), nullable=False)
    phone = Column(String(20), nullable=True)
    email = Column(String(200), nullable=True)
    
    # Priority (1-5, where 1 is highest priority)
    priority = Column(Integer, nullable=False, default=5)
    
    # Status
    is_active = Column(Boolean, nullable=False, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class SOSContactNotification(Base):
    """Track which contacts were notified for each SOS request."""
    __tablename__ = "sos_contact_notifications"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sos_request_id = Column(UUID(as_uuid=True), ForeignKey("sos_requests.id", ondelete="CASCADE"), nullable=False, index=True)
    contact_id = Column(UUID(as_uuid=True), ForeignKey("emergency_contacts.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Notification status
    notification_sent = Column(Boolean, nullable=False, default=False)
    notification_id = Column(UUID(as_uuid=True), nullable=True)  # From notification service
    
    # Timestamp
    notified_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    sos_request = relationship("SOSRequest", back_populates="contacts_notified")
    contact = relationship("EmergencyContact")


class EmergencyNumber(Base):
    """Configurable emergency numbers (for future multi-country support)."""
    __tablename__ = "emergency_numbers"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Country/region code
    country_code = Column(String(10), nullable=True)  # e.g., "US", "IN", "EU"
    
    # Emergency number
    number = Column(String(20), nullable=False)  # e.g., "112", "911", "100"
    
    # Description
    description = Column(String(200), nullable=True)  # e.g., "Police Emergency"
    
    # Status
    is_active = Column(Boolean, nullable=False, default=True)
    is_default = Column(Boolean, nullable=False, default=False)  # Default emergency number
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
