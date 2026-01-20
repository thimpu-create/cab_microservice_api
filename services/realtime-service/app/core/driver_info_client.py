"""
Client to fetch driver information (ratings, vehicle types) from driver service.
Used by matching algorithm.
"""
import httpx
from typing import Dict, List, Optional
from uuid import UUID

from app.core.config import settings


class DriverInfoClient:
    """Client for fetching driver information from driver service."""
    
    def __init__(self):
        self.base_url = settings.DRIVER_SERVICE_URL
        self.timeout = 5.0
    
    async def get_driver_info(self, driver_id: str) -> Optional[Dict]:
        """Get information for a single driver."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/drivers/{driver_id}/info",
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    print(f"⚠️ Failed to get driver info for {driver_id}: {response.status_code}")
                    return None
                    
        except httpx.RequestError as e:
            print(f"⚠️ Error fetching driver info: {e}")
            return None
    
    async def get_drivers_batch_info(self, driver_ids: List[str]) -> Dict[str, Dict]:
        """
        Get information for multiple drivers at once.
        Returns dict mapping driver_id -> driver_info
        """
        if not driver_ids:
            return {}
        
        try:
            async with httpx.AsyncClient() as client:
                # Convert string IDs to UUIDs for the API
                driver_uuids = [UUID(driver_id) for driver_id in driver_ids]
                
                response = await client.post(
                    f"{self.base_url}/drivers/batch/info",
                    json=driver_uuids,
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    data = response.json()
                    drivers_list = data.get("drivers", [])
                    
                    # Convert to dict for easy lookup
                    return {
                        driver_info["driver_id"]: driver_info
                        for driver_info in drivers_list
                    }
                else:
                    print(f"⚠️ Failed to get batch driver info: {response.status_code}")
                    return {}
                    
        except (httpx.RequestError, ValueError) as e:
            print(f"⚠️ Error fetching batch driver info: {e}")
            return {}


# Global driver info client instance
driver_info_client = DriverInfoClient()
