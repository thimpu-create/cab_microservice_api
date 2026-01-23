"""
Pricing calculation endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID

from app.db.session import get_db
from app.schemas.pricing import FareCalculationRequest, FareCalculationResponse
from app.core.pricing_engine import PricingEngine
from app.core.security import get_current_user_id

router = APIRouter(prefix="/pricing", tags=["Pricing"])


@router.post("/calculate", response_model=FareCalculationResponse, status_code=status.HTTP_200_OK)
async def calculate_fare(
    request: FareCalculationRequest,
    db: Session = Depends(get_db),
    user_id: Optional[UUID] = Depends(get_current_user_id)
):
    """
    Calculate fare for a ride.
    
    - Calculates distance if not provided
    - Estimates duration if not provided
    - Applies base pricing, peak hours, surge, and regulatory constraints
    - Returns detailed breakdown
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
            estimated_distance_km=request.estimated_distance_km,
            estimated_duration_minutes=request.estimated_duration_minutes,
            user_id=str(user_id) if user_id else None
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error calculating fare: {str(e)}"
        )


@router.get("/history/{request_id}", response_model=FareCalculationResponse, status_code=status.HTTP_200_OK)
async def get_pricing_history(
    request_id: str,
    db: Session = Depends(get_db)
):
    """Get pricing calculation details by request ID."""
    from app.db.models import PricingCalculation
    
    calculation = db.query(PricingCalculation).filter(
        PricingCalculation.request_id == request_id
    ).first()
    
    if not calculation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pricing calculation not found"
        )
    
    # Reconstruct response from calculation
    return {
        "base_fare": calculation.base_fare,
        "distance_cost": calculation.distance_cost,
        "time_cost": calculation.time_cost,
        "subtotal": calculation.subtotal,
        "peak_multiplier": calculation.peak_multiplier,
        "peak_adjusted_subtotal": calculation.subtotal * calculation.peak_multiplier,
        "surge_multiplier": calculation.surge_multiplier,
        "surge_adjusted_subtotal": calculation.subtotal * calculation.peak_multiplier * calculation.surge_multiplier,
        "minimum_fare": 0,  # Would need to store this
        "regulatory_cap": None,  # Would need to store this
        "final_fare": calculation.final_fare,
        "currency": "INR",
        "breakdown": {
            "base": calculation.base_fare,
            "distance": calculation.distance_cost,
            "time": calculation.time_cost
        },
        "metadata": {
            "distance_km": calculation.distance_km,
            "duration_minutes": calculation.duration_minutes,
            "vehicle_type": calculation.vehicle_type.value,
            "city_code": calculation.city_code or "",
            "minimum_fare_applied": calculation.minimum_fare_applied,
            "regulatory_cap_applied": calculation.regulatory_cap_applied
        }
    }
