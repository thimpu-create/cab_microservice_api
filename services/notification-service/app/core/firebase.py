import firebase_admin
from firebase_admin import credentials, messaging
from typing import List, Dict, Any, Optional
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

# Initialize Firebase Admin SDK
def initialize_firebase():
    """Initialize Firebase Admin SDK."""
    try:
        # Try to get the certificate path
        cert_path = os.getenv("FIREBASE_KEY_PATH", "firebase-key.json")
        
        # If relative path, make it absolute from the app root
        if not os.path.isabs(cert_path):
            # Get the absolute path relative to this file's location
            service_dir = Path(__file__).parent.parent.parent
            cert_path = service_dir / cert_path
        
        if not os.path.exists(cert_path):
            raise FileNotFoundError(f"Firebase key not found at {cert_path}")
        
        cred = credentials.Certificate(str(cert_path))
        
        # Check if app is already initialized
        if not firebase_admin._apps:
            firebase_admin.initialize_app(cred)
            logger.info("✅ Firebase Admin SDK initialized successfully")
        else:
            logger.info("✅ Firebase Admin SDK already initialized")
    except Exception as e:
        logger.error(f"❌ Failed to initialize Firebase: {str(e)}")
        raise


# Initialize on import
initialize_firebase()


class FirebaseService:
    """Service for Firebase Cloud Messaging operations."""
    
    @staticmethod
    def send_push_notification(
        device_token: str,
        title: str,
        body: str,
        data: Optional[Dict[str, Any]] = None,
        priority: str = "high"
    ) -> Dict[str, Any]:
        """
        Send a push notification to a single device.
        
        Args:
            device_token: FCM device token
            title: Notification title
            body: Notification body/message
            data: Additional data to send
            priority: Priority level (high, normal)
        
        Returns:
            Dict with message_id or error information
        """
        try:
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body,
                ),
                data=data or {},
                token=device_token,
                android=messaging.AndroidConfig(
                    priority=priority,
                    notification=messaging.AndroidNotification(
                        sound="default",
                        click_action="FLUTTER_NOTIFICATION_CLICK",
                    ),
                ),
                apns=messaging.APNSConfig(
                    headers={"apns-priority": "10" if priority == "high" else "5"},
                    payload=messaging.APNSPayload(
                        aps=messaging.Aps(
                            alert=messaging.ApsAlert(
                                title=title,
                                body=body,
                            ),
                            sound="default",
                            custom_data=data or {},
                        ),
                    ),
                ),
                webpush=messaging.WebpushConfig(
                    data=data or {},
                ),
            )
            
            response = messaging.send(message)
            logger.info(f"✅ Push notification sent: {response}")
            return {"success": True, "message_id": response}
        
        except Exception as e:
            logger.error(f"❌ Failed to send push notification: {str(e)}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def send_multicast_notification(
        device_tokens: List[str],
        title: str,
        body: str,
        data: Optional[Dict[str, Any]] = None,
        priority: str = "high"
    ) -> Dict[str, Any]:
        """
        Send a push notification to multiple devices.
        
        Args:
            device_tokens: List of FCM device tokens
            title: Notification title
            body: Notification body/message
            data: Additional data to send
            priority: Priority level
        
        Returns:
            Dict with results for each token
        """
        try:
            if not device_tokens:
                return {"success": False, "error": "No device tokens provided"}
            
            message = messaging.MulticastMessage(
                notification=messaging.Notification(
                    title=title,
                    body=body,
                ),
                data=data or {},
                tokens=device_tokens,
                android=messaging.AndroidConfig(
                    priority=priority,
                    notification=messaging.AndroidNotification(
                        sound="default",
                        click_action="FLUTTER_NOTIFICATION_CLICK",
                    ),
                ),
                apns=messaging.APNSConfig(
                    headers={"apns-priority": "10" if priority == "high" else "5"},
                    payload=messaging.APNSPayload(
                        aps=messaging.Aps(
                            alert=messaging.ApsAlert(
                                title=title,
                                body=body,
                            ),
                            sound="default",
                            custom_data=data or {},
                        ),
                    ),
                ),
            )
            
            response = messaging.send_multicast(message)
            logger.info(f"✅ Multicast notification sent to {response.success_count} devices")
            
            return {
                "success": True,
                "success_count": response.success_count,
                "failure_count": response.failure_count,
                "responses": [resp.message_id if hasattr(resp, 'message_id') else str(resp.exception) 
                             for resp in response.responses]
            }
        
        except Exception as e:
            logger.error(f"❌ Failed to send multicast notification: {str(e)}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def subscribe_to_topic(device_tokens: List[str], topic: str) -> Dict[str, Any]:
        """
        Subscribe device tokens to a Firebase Cloud Messaging topic.
        
        Args:
            device_tokens: List of FCM device tokens
            topic: Topic name to subscribe to
        
        Returns:
            Operation result
        """
        try:
            if not device_tokens:
                return {"success": False, "error": "No device tokens provided"}
            
            response = messaging.make_topic_management_request(
                messaging.TopicMgtRequest(
                    operation="Subscribe",
                    tokens=device_tokens,
                    topic=topic
                )
            )
            
            logger.info(f"✅ Subscribed {len(device_tokens)} devices to topic '{topic}'")
            return {"success": True, "subscribed": len(device_tokens), "topic": topic}
        
        except Exception as e:
            logger.error(f"❌ Failed to subscribe to topic: {str(e)}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def unsubscribe_from_topic(device_tokens: List[str], topic: str) -> Dict[str, Any]:
        """
        Unsubscribe device tokens from a Firebase Cloud Messaging topic.
        
        Args:
            device_tokens: List of FCM device tokens
            topic: Topic name to unsubscribe from
        
        Returns:
            Operation result
        """
        try:
            if not device_tokens:
                return {"success": False, "error": "No device tokens provided"}
            
            response = messaging.make_topic_management_request(
                messaging.TopicMgtRequest(
                    operation="Unsubscribe",
                    tokens=device_tokens,
                    topic=topic
                )
            )
            
            logger.info(f"✅ Unsubscribed {len(device_tokens)} devices from topic '{topic}'")
            return {"success": True, "unsubscribed": len(device_tokens), "topic": topic}
        
        except Exception as e:
            logger.error(f"❌ Failed to unsubscribe from topic: {str(e)}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def send_to_topic(
        topic: str,
        title: str,
        body: str,
        data: Optional[Dict[str, Any]] = None,
        priority: str = "high"
    ) -> Dict[str, Any]:
        """
        Send a notification to all subscribers of a topic.
        
        Args:
            topic: Topic name
            title: Notification title
            body: Notification body/message
            data: Additional data to send
            priority: Priority level
        
        Returns:
            Message response
        """
        try:
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body,
                ),
                data=data or {},
                topic=topic,
                android=messaging.AndroidConfig(
                    priority=priority,
                ),
                apns=messaging.APNSConfig(
                    headers={"apns-priority": "10" if priority == "high" else "5"},
                ),
            )
            
            response = messaging.send(message)
            logger.info(f"✅ Topic notification sent to '{topic}': {response}")
            return {"success": True, "message_id": response}
        
        except Exception as e:
            logger.error(f"❌ Failed to send topic notification: {str(e)}")
            return {"success": False, "error": str(e)}