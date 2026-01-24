"""
Client to fetch company information from company-service.
Used to get company_id for VendorAdmin users.
"""
import httpx
from typing import Optional
from uuid import UUID
from app.core.config import settings

COMPANY_SERVICE_URL = settings.COMPANY_SERVICE_URL


async def get_user_company_id(user_id: UUID) -> Optional[UUID]:
    """
    Get company_id for a VendorAdmin user from company-service.
    Gets the company where user is the owner (owner_user_id = user_id).
    
    Returns:
        company_id if user owns a company, None otherwise
    """
    try:
        async with httpx.AsyncClient() as client:
            # Get company owned by user
            response = await client.get(
                f"{COMPANY_SERVICE_URL}/companies/owned-by/{user_id}",
                timeout=5.0
            )
            
            if response.status_code == 200:
                company = response.json()
                company_id_str = company.get("id")
                if company_id_str:
                    return UUID(company_id_str)
                return None
            elif response.status_code == 404:
                # User doesn't own a company
                return None
            else:
                print(f"⚠️ Failed to get company: {response.status_code}")
                return None
                
    except httpx.RequestError as e:
        print(f"⚠️ Failed to connect to company-service: {e}")
        return None
    except Exception as e:
        print(f"⚠️ Error getting user company_id: {e}")
        return None
