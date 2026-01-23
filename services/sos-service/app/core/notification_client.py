"""
Notification client for sos-service.
Sends emergency alerts to emergency contacts via notification service.
"""
import httpx
from typing import List, Optional
from uuid import UUID
from app.core.config import settings


class NotificationClient:
    """Client for sending notifications via notification service."""
    
    def __init__(self):
        self.base_url = settings.NOTIFICATION_SERVICE_URL
        self.timeout = 10.0
    
    async def send_sos_alert(
        self,
        user_ids: List[UUID],
        user_name: str,
        latitude: float,
        longitude: float,
        sos_id: str,
        emergency_number: str = "112"
    ) -> bool:
        """
        Send SOS emergency alert to multiple emergency contacts.
        
        Args:
            user_ids: List of emergency contact user IDs
            user_name: Name of the user who triggered SOS
            latitude: User's current latitude
            longitude: User's current longitude
            sos_id: SOS request ID
            emergency_number: Emergency number used (default: 112)
        
        Returns:
            True if notifications sent successfully, False otherwise
        """
        try:
            # Create map link (Google Maps)
            map_link = f"https://www.google.com/maps?q={latitude},{longitude}"
            
            # Create notification message
            message = (
                f"🚨 EMERGENCY SOS ALERT 🚨\n\n"
                f"{user_name} has triggered an emergency SOS.\n\n"
                f"📍 Location: {latitude}, {longitude}\n"
                f"🔗 Map: {map_link}\n"
                f"📞 Emergency Number: {emergency_number}\n\n"
                f"Please check on them immediately!"
            )
            
            async with httpx.AsyncClient() as client:
                # Use bulk notification endpoint
                response = await client.post(
                    f"{self.base_url}/notifications/send/bulk",
                    json={
                        "user_ids": [str(uid) for uid in user_ids],
                        "notification_type": "sos_alert",  # Will need to add this to NotificationType enum
                        "title": "🚨 Emergency SOS Alert",
                        "message": message,
                        "channels": ["sms", "push", "in_app"],  # High priority - use all channels
                        "data": {
                            "sos_id": sos_id,
                            "user_name": user_name,
                            "latitude": latitude,
                            "longitude": longitude,
                            "map_link": map_link,
                            "emergency_number": emergency_number
                        },
                        "priority": "urgent"
                    },
                    timeout=self.timeout
                )
                
                if response.status_code in [200, 201]:
                    print(f"✅ SOS alerts sent to {len(user_ids)} contacts")
                    return True
                else:
                    print(f"⚠️ Failed to send SOS alerts: {response.status_code} - {response.text}")
                    return False
                    
        except httpx.RequestError as e:
            print(f"⚠️ Failed to connect to notification service: {e}")
            return False
        except Exception as e:
            print(f"⚠️ Unexpected error sending SOS alerts: {e}")
            return False
