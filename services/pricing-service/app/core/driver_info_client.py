"""
Client to fetch driver information from driver-service.
Used to get company_id to determine pricing type.
"""
import httpx
from typing import Optional
from uuid import UUID
from app.core.config import settings

DRIVER_SERVICE_URL = settings.DRIVER_SERVICE_URL


async def get_driver_company_id(driver_id: UUID) -> Optional[UUID]:
    """
    Get driver's company_id from driver-service.
    
    Returns:
        company_id if driver belongs to a company, None if independent driver
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{DRIVER_SERVICE_URL}/drivers/{driver_id}/info",
                timeout=5.0
            )
            
            if response.status_code == 200:
                driver_info = response.json()
                # Check if driver-service returns company_id
                # If not, we might need to add it to the driver_info endpoint
                company_id_str = driver_info.get("company_id")
                if company_id_str:
                    return UUID(company_id_str)
                return None
            else:
                print(f"⚠️ Failed to get driver info: {response.status_code}")
                return None
                
    except httpx.RequestError as e:
        print(f"⚠️ Failed to connect to driver-service: {e}")
        return None
    except Exception as e:
        print(f"⚠️ Error getting driver company_id: {e}")
        return None
