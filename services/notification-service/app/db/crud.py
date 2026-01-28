"""
CRUD operations for device management.
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_
from uuid import UUID
from datetime import datetime, timedelta
import logging
from app.db.models import UserDevice, NotificationLog

logger = logging.getLogger(__name__)


class DeviceCRUD:
    """CRUD operations for user devices."""

    @staticmethod
    def register_device(
        db: Session,
        user_id: UUID,
        device_token: str,
        device_name: str,
        platform: str
    ) -> UserDevice:
        """
        Register or update a device token for a user.
        
        Args:
            db: Database session
            user_id: User ID from auth service
            device_token: FCM device token
            device_name: Device name (e.g., "iPhone 15")
            platform: Platform (ios, android, web)
        
        Returns:
            UserDevice object
        """
        try:
            # Check if token already exists
            existing_device = db.query(UserDevice).filter(
                UserDevice.device_token == device_token
            ).first()

            if existing_device:
                # Update existing device
                existing_device.user_id = user_id
                existing_device.device_name = device_name
                existing_device.platform = platform
                existing_device.is_active = True
                existing_device.last_heartbeat = datetime.utcnow()
                existing_device.updated_at = datetime.utcnow()
                db.commit()
                logger.info(f"✅ Updated device token for user {user_id}")
                return existing_device
            
            # Create new device
            new_device = UserDevice(
                user_id=user_id,
                device_token=device_token,
                device_name=device_name,
                platform=platform,
                is_active=True,
                last_heartbeat=datetime.utcnow()
            )
            db.add(new_device)
            db.commit()
            db.refresh(new_device)
            logger.info(f"✅ Registered new device for user {user_id}")
            return new_device
        
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Error registering device: {e}")
            raise

    @staticmethod
    def get_user_devices(
        db: Session,
        user_id: UUID,
        active_only: bool = True
    ) -> list[UserDevice]:
        """
        Get all devices for a user.
        
        Args:
            db: Database session
            user_id: User ID
            active_only: Only return active devices
        
        Returns:
            List of UserDevice objects
        """
        query = db.query(UserDevice).filter(UserDevice.user_id == user_id)
        
        if active_only:
            query = query.filter(UserDevice.is_active == True)
        
        devices = query.all()
        logger.info(f"📱 Retrieved {len(devices)} devices for user {user_id}")
        return devices

    @staticmethod
    def get_user_device_tokens(
        db: Session,
        user_id: UUID,
        active_only: bool = True
    ) -> list[str]:
        """
        Get all device tokens for a user (for Firebase).
        
        Args:
            db: Database session
            user_id: User ID
            active_only: Only return active devices
        
        Returns:
            List of FCM device tokens
        """
        devices = DeviceCRUD.get_user_devices(db, user_id, active_only)
        tokens = [device.device_token for device in devices]
        return tokens

    @staticmethod
    def get_devices_by_platform(
        db: Session,
        user_id: UUID,
        platform: str,
        active_only: bool = True
    ) -> list[UserDevice]:
        """
        Get devices for a user by platform.
        
        Args:
            db: Database session
            user_id: User ID
            platform: Platform (ios, android, web)
            active_only: Only return active devices
        
        Returns:
            List of UserDevice objects
        """
        query = db.query(UserDevice).filter(
            and_(
                UserDevice.user_id == user_id,
                UserDevice.platform == platform
            )
        )
        
        if active_only:
            query = query.filter(UserDevice.is_active == True)
        
        return query.all()

    @staticmethod
    def deactivate_device(db: Session, device_id: UUID) -> bool:
        """
        Deactivate a device (soft delete).
        
        Args:
            db: Database session
            device_id: Device ID to deactivate
        
        Returns:
            True if successful
        """
        try:
            device = db.query(UserDevice).filter(UserDevice.id == device_id).first()
            if not device:
                logger.warning(f"Device {device_id} not found")
                return False
            
            device.is_active = False
            device.updated_at = datetime.utcnow()
            db.commit()
            logger.info(f"✅ Deactivated device {device_id}")
            return True
        
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Error deactivating device: {e}")
            return False

    @staticmethod
    def delete_device(db: Session, device_id: UUID) -> bool:
        """
        Permanently delete a device.
        
        Args:
            db: Database session
            device_id: Device ID to delete
        
        Returns:
            True if successful
        """
        try:
            device = db.query(UserDevice).filter(UserDevice.id == device_id).first()
            if not device:
                logger.warning(f"Device {device_id} not found")
                return False
            
            db.delete(device)
            db.commit()
            logger.info(f"✅ Deleted device {device_id}")
            return True
        
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Error deleting device: {e}")
            return False

    @staticmethod
    def heartbeat(db: Session, device_token: str) -> bool:
        """
        Update last heartbeat for a device (used to track active devices).
        
        Args:
            db: Database session
            device_token: Device token
        
        Returns:
            True if successful
        """
        try:
            device = db.query(UserDevice).filter(
                UserDevice.device_token == device_token
            ).first()
            
            if not device:
                return False
            
            device.last_heartbeat = datetime.utcnow()
            db.commit()
            return True
        
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Error updating heartbeat: {e}")
            return False

    @staticmethod
    def cleanup_inactive_devices(db: Session, days: int = 30) -> int:
        """
        Deactivate devices with no heartbeat for specified days.
        
        Args:
            db: Database session
            days: Number of days of inactivity before deactivation
        
        Returns:
            Number of devices deactivated
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            devices = db.query(UserDevice).filter(
                and_(
                    UserDevice.is_active == True,
                    UserDevice.last_heartbeat < cutoff_date
                )
            ).all()
            
            count = len(devices)
            for device in devices:
                device.is_active = False
                device.updated_at = datetime.utcnow()
            
            db.commit()
            logger.info(f"✅ Deactivated {count} inactive devices")
            return count
        
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Error cleaning up devices: {e}")
            return 0


class NotificationLogCRUD:
    """CRUD operations for notification logs."""

    @staticmethod
    def log_notification(
        db: Session,
        user_id: UUID,
        notification_type: str,
        title: str,
        message: str,
        channels: str,
        device_id: UUID = None,
        fcm_message_id: str = None,
        status: str = "sent",
        error_message: str = None
    ) -> NotificationLog:
        """
        Log a sent notification.
        
        Args:
            db: Database session
            user_id: User ID
            notification_type: Type of notification
            title: Notification title
            message: Notification message
            channels: Channels used (comma-separated)
            device_id: Device ID (if applicable)
            fcm_message_id: Firebase message ID
            status: Status (sent, failed, pending)
            error_message: Error message if failed
        
        Returns:
            NotificationLog object
        """
        try:
            log = NotificationLog(
                user_id=user_id,
                device_id=device_id,
                notification_type=notification_type,
                title=title,
                message=message,
                channels=channels,
                fcm_message_id=fcm_message_id,
                status=status,
                error_message=error_message
            )
            db.add(log)
            db.commit()
            db.refresh(log)
            return log
        
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Error logging notification: {e}")
            raise

    @staticmethod
    def get_user_notifications(
        db: Session,
        user_id: UUID,
        limit: int = 100,
        days: int = 30
    ) -> list[NotificationLog]:
        """
        Get notification history for a user.
        
        Args:
            db: Database session
            user_id: User ID
            limit: Maximum results
            days: Only get notifications from last N days
        
        Returns:
            List of NotificationLog objects
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        logs = db.query(NotificationLog).filter(
            and_(
                NotificationLog.user_id == user_id,
                NotificationLog.created_at >= cutoff_date
            )
        ).order_by(NotificationLog.created_at.desc()).limit(limit).all()
        
        return logs

    @staticmethod
    def get_failed_notifications(
        db: Session,
        limit: int = 100
    ) -> list[NotificationLog]:
        """
        Get failed notifications for debugging.
        
        Args:
            db: Database session
            limit: Maximum results
        
        Returns:
            List of NotificationLog objects
        """
        logs = db.query(NotificationLog).filter(
            NotificationLog.status == "failed"
        ).order_by(NotificationLog.created_at.desc()).limit(limit).all()
        
        return logs

    @staticmethod
    def get_notification_stats(db: Session, days: int = 7) -> dict:
        """
        Get notification statistics.
        
        Args:
            db: Database session
            days: Time period for stats
        
        Returns:
            Dict with statistics
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        total = db.query(NotificationLog).filter(
            NotificationLog.created_at >= cutoff_date
        ).count()
        
        sent = db.query(NotificationLog).filter(
            and_(
                NotificationLog.status == "sent",
                NotificationLog.created_at >= cutoff_date
            )
        ).count()
        
        failed = db.query(NotificationLog).filter(
            and_(
                NotificationLog.status == "failed",
                NotificationLog.created_at >= cutoff_date
            )
        ).count()
        
        return {
            "total": total,
            "sent": sent,
            "failed": failed,
            "period_days": days,
            "success_rate": (sent / total * 100) if total > 0 else 0
        }
