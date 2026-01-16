from fastapi import APIRouter, HTTPException, Depends, status
import httpx
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from uuid import UUID

router = APIRouter(prefix="/drivers", tags=["Drivers"])

DRIVER_SERVICE_URL = "http://driver-service:8000/api/v1/drivers"
# DRIVER_SERVICE_URL = "http://localhost:8003/api/v1/drivers"

security = HTTPBearer()


def get_auth_header(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)):
    """Get authorization header if provided (for optional auth endpoints)"""
    if credentials:
        return {"Authorization": f"Bearer {credentials.credentials}"}
    return {}


# ======================================================
# COMPANY DRIVER ENDPOINTS (Require Authentication)
# ======================================================

@router.get("/company/{company_id}/count")
async def get_driver_count_for_company(
    company_id: UUID,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Get driver count statistics for a specific company."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{DRIVER_SERVICE_URL}/company/{company_id}/count",
                headers={"Authorization": f"Bearer {credentials.credentials}"},
                timeout=10.0
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Driver service unavailable: {str(e)}"
            )
    
    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code,
            detail=response.json().get("detail", "Unknown error")
        )
    
    return response.json()


@router.get("/company/{company_id}")
async def get_drivers_for_company(
    company_id: UUID,
    skip: int = 0,
    limit: int = 100,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Get list of drivers for a specific company."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{DRIVER_SERVICE_URL}/company/{company_id}",
                headers={"Authorization": f"Bearer {credentials.credentials}"},
                params={"skip": skip, "limit": limit},
                timeout=10.0
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Driver service unavailable: {str(e)}"
            )
    
    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code,
            detail=response.json().get("detail", "Unknown error")
        )
    
    return response.json()


@router.post("/company/{company_id}/register")
async def register_driver_for_company(
    company_id: UUID,
    payload: dict,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Register a new driver for a company."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{DRIVER_SERVICE_URL}/company/{company_id}/register",
                json=payload,
                headers={"Authorization": f"Bearer {credentials.credentials}"},
                timeout=10.0
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Driver service unavailable: {str(e)}"
            )
    
    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code,
            detail=response.json().get("detail", "Unknown error")
        )
    
    return response.json()


# ======================================================
# INDEPENDENT DRIVER ENDPOINTS (Public - No Auth)
# ======================================================

@router.post("/register/independent")
async def register_independent_driver(payload: dict):
    """Register as an independent driver (public endpoint, no authentication required)."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{DRIVER_SERVICE_URL}/register/independent",
                json=payload,
                timeout=10.0
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Driver service unavailable: {str(e)}"
            )
    
    if response.status_code != 200 and response.status_code != 201:
        raise HTTPException(
            status_code=response.status_code,
            detail=response.json().get("detail", "Unknown error")
        )
    
    return response.json()
