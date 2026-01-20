"""
Notification client for realtime-service.
Centralizes all notification calls to the notification service.
"""
import httpx
from typing import Optional, List, Dict, Any
from uuid import UUID

from app.core.config import settings


class NotificationClient:
    """Client for sending notifications via notification service."""
    
    def __init__(self):
        self.base_url = settings.NOTIFICATION_SERVICE_URL
        self.timeout = 10.0
    
    async def _send_request(
        self,
        endpoint: str,
        data: dict,
        method: str = "POST"
    ) -> Optional[dict]:
        """Internal method to send HTTP requests to notification service."""
        try:
            async with httpx.AsyncClient() as client:
                url = f"{self.base_url}{endpoint}"
                
                if method == "POST":
                    response = await client.post(url, json=data, timeout=self.timeout)
                else:
                    response = await client.get(url, timeout=self.timeout)
                
                if response.status_code in [200, 201]:
                    return response.json()
                else:
                    print(f"⚠️ Notification service error: {response.status_code} - {response.text}")
                    return None
                    
        except httpx.RequestError as e:
            print(f"⚠️ Failed to connect to notification service: {e}")
            return None
        except Exception as e:
            print(f"⚠️ Unexpected error sending notification: {e}")
            return None
    
    async def notify_ride_request_sent(
        self,
        driver_ids: List[str],
        passenger_id: str,
        request_id: str,
        pickup_lat: float,
        pickup_lon: float,
        distance_km: float,
        pickup_address: Optional[str] = None
    ) -> bool:
        """
        Notify multiple drivers about a new ride request.
        """
        data = {
            "driver_ids": driver_ids,
            "passenger_id": passenger_id,
            "request_id": request_id,
            "pickup_lat": pickup_lat,
            "pickup_lon": pickup_lon,
            "distance_km": distance_km,
            "pickup_address": pickup_address
        }
        
        result = await self._send_request("/notifications/ride/request-sent", data)
        return result is not None
    
    async def notify_driver_assigned(
        self,
        passenger_id: str,
        driver_id: str,
        request_id: str,
        pickup_lat: float,
        pickup_lon: float,
        dropoff_lat: Optional[float] = None,
        dropoff_lon: Optional[float] = None
    ) -> bool:
        """
        Notify passenger that a driver has been assigned.
        """
        data = {
            "passenger_id": passenger_id,
            "driver_id": driver_id,
            "request_id": request_id,
            "pickup_lat": pickup_lat,
            "pickup_lon": pickup_lon
        }
        
        result = await self._send_request("/notifications/ride/driver-assigned", data)
        return result is not None
    
    async def notify_ride_started(
        self,
        passenger_id: str,
        driver_id: str,
        request_id: str
    ) -> bool:
        """
        Notify passenger that ride has started.
        """
        data = {
            "user_id": passenger_id,
            "notification_type": "ride_started",
            "request_id": request_id,
            "title": "Ride Started",
            "message": "Your driver has started the ride",
            "additional_data": {
                "driver_id": driver_id
            }
        }
        
        result = await self._send_request("/notifications/ride/status-update", data)
        return result is not None
    
    async def notify_ride_completed(
        self,
        passenger_id: str,
        driver_id: str,
        request_id: str
    ) -> bool:
        """
        Notify passenger that ride has been completed.
        """
        data = {
            "user_id": passenger_id,
            "notification_type": "ride_completed",
            "request_id": request_id,
            "title": "Ride Completed",
            "message": "Your ride has been completed. Thank you!",
            "additional_data": {
                "driver_id": driver_id
            }
        }
        
        result = await self._send_request("/notifications/ride/status-update", data)
        return result is not None
    
    async def notify_ride_cancelled(
        self,
        user_id: str,
        cancelled_by: str,  # "passenger" or "driver"
        request_id: str,
        other_party_id: Optional[str] = None
    ) -> bool:
        """
        Notify user that ride has been cancelled.
        """
        if cancelled_by == "passenger":
            title = "Ride Cancelled"
            message = "The passenger cancelled the ride"
        else:
            title = "Ride Cancelled"
            message = "The driver cancelled the ride"
        
        data = {
            "user_id": user_id,
            "notification_type": "ride_cancelled",
            "request_id": request_id,
            "title": title,
            "message": message,
            "additional_data": {
                "cancelled_by": cancelled_by
            }
        }
        
        result = await self._send_request("/notifications/ride/status-update", data)
        return result is not None
    
    async def notify_ride_expired(
        self,
        passenger_id: str,
        request_id: str
    ) -> bool:
        """
        Notify passenger that ride request has expired.
        """
        data = {
            "user_id": passenger_id,
            "notification_type": "ride_expired",
            "request_id": request_id,
            "title": "Ride Request Expired",
            "message": "No driver accepted your ride request in time. Please try again.",
            "additional_data": {}
        }
        
        result = await self._send_request("/notifications/ride/status-update", data)
        return result is not None
    
    async def send_custom_notification(
        self,
        user_id: str,
        notification_type: str,
        title: str,
        message: str,
        data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Send a custom notification.
        """
        payload = {
            "user_id": user_id,
            "notification_type": notification_type,
            "request_id": data.get("request_id", "") if data else "",
            "title": title,
            "message": message,
            "additional_data": data or {}
        }
        
        result = await self._send_request("/notifications/ride/status-update", payload)
        return result is not None


# Global notification client instance
notification_client = NotificationClient()
