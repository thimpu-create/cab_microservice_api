"""
Database models for notification service.
"""
from sqlalchemy import Column, String, Boolean, DateTime, UUID, Index
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import uuid

Base = declarative_base()


class UserDevice(Base):
    """Store user device information and FCM tokens."""
    __tablename__ = "user_devices"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID, nullable=False, index=True)  # Reference to auth-service user
    device_token = Column(String, unique=True, nullable=False, index=True)  # FCM token
    device_name = Column(String, nullable=True)  # e.g., "iPhone 15", "Samsung S24"
    platform = Column(String, nullable=False)  # "ios", "android", "web"
    is_active = Column(Boolean, default=True, index=True)  # Soft delete / deactivation
    last_heartbeat = Column(DateTime, default=datetime.utcnow)  # Last activity
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_user_active', 'user_id', 'is_active'),
        Index('idx_platform', 'platform'),
        Index('idx_user_platform', 'user_id', 'platform'),
    )

    def __repr__(self):
        return f"<UserDevice(user_id={self.user_id}, device_name={self.device_name}, platform={self.platform})>"


class NotificationLog(Base):
    """Log of sent notifications for tracking and analytics."""
    __tablename__ = "notification_logs"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID, nullable=False, index=True)
    device_id = Column(UUID, nullable=True)  # Reference to UserDevice
    notification_type = Column(String, nullable=False)  # ride_request, driver_assigned, etc.
    title = Column(String, nullable=False)
    message = Column(String, nullable=False)
    channels = Column(String, nullable=False)  # JSON string or CSV
    fcm_message_id = Column(String, nullable=True)  # Firebase response
    status = Column(String, default="sent")  # sent, failed, pending
    error_message = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    __table_args__ = (
        Index('idx_user_created', 'user_id', 'created_at'),
        Index('idx_type_created', 'notification_type', 'created_at'),
        Index('idx_status', 'status'),
    )

    def __repr__(self):
        return f"<NotificationLog(user_id={self.user_id}, type={self.notification_type}, status={self.status})>"
