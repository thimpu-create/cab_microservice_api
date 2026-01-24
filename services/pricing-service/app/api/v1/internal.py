"""
Internal endpoints for service-to-service calls (no JWT).
Protected by X-Internal-Key header when INTERNAL_API_KEY is set.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.pricing import FareCalculationRequest, FareCalculationResponse
from app.core.pricing_engine import PricingEngine
from app.core.config import settings

router = APIRouter(prefix="/internal", tags=["Internal"])


def verify_internal_key(x_internal_key: Optional[str] = Header(None, alias="X-Internal-Key")):
    if not settings.INTERNAL_API_KEY:
        return True  # Dev: no key configured, allow
    if x_internal_key != settings.INTERNAL_API_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid internal key")
    return True


@router.post("/estimate", response_model=FareCalculationResponse, status_code=status.HTTP_200_OK)
async def estimate_fare(
    request: FareCalculationRequest,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_internal_key),
):
    """
    Calculate fare estimate (no JWT).
    Used by realtime-service when creating ride requests.
    """
    try:
        engine = PricingEngine(db)
        result = await engine.calculate_fare(
            pickup_lat=request.pickup_lat,
            pickup_lon=request.pickup_lon,
            dropoff_lat=request.dropoff_lat,
            dropoff_lon=request.dropoff_lon,
            vehicle_type=request.vehicle_type,
            city_code=request.city_code,
            driver_id=request.driver_id,
            company_id=request.company_id,
            estimated_distance_km=request.estimated_distance_km,
            estimated_duration_minutes=request.estimated_duration_minutes,
            request_id=None,
            user_id=None,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error calculating fare: {str(e)}",
        )
