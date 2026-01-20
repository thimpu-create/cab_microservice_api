from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from uuid import UUID
from typing import List, Optional

from app.db.session import get_db
from app.db.models import Driver, DriverRating, VehicleType

router = APIRouter(prefix="/drivers", tags=["Driver Information"])


@router.get("/{driver_id}/info", response_model=dict)
async def get_driver_info(
    driver_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get comprehensive driver information including rating and vehicle type.
    Used by realtime-service for matching algorithm.
    """
    driver = db.query(Driver).filter(Driver.id == driver_id).first()
    if not driver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Driver not found"
        )
    
    # Get average rating
    avg_rating_result = db.query(func.avg(DriverRating.rating)).filter(
        DriverRating.driver_id == driver_id
    ).scalar()
    average_rating = round(float(avg_rating_result or 0.0), 2)
    total_ratings = db.query(DriverRating).filter(DriverRating.driver_id == driver_id).count()
    
    return {
        "driver_id": str(driver.id),
        "user_id": str(driver.user_id),
        "vehicle_type": driver.vehicle_type.value if driver.vehicle_type else None,
        "average_rating": average_rating,
        "total_ratings": total_ratings,
        "is_active": driver.is_active,
        "is_verified": driver.is_verified,
        "status": driver.status.value if driver.status else None,
        "vehicle_make": driver.vehicle_make,
        "vehicle_model": driver.vehicle_model,
    }


@router.post("/batch/info", response_model=dict)
async def get_drivers_batch_info(
    driver_ids: List[UUID],
    db: Session = Depends(get_db)
):
    """
    Get information for multiple drivers at once.
    Optimized for matching algorithm to fetch ratings and vehicle types.
    """
    drivers = db.query(Driver).filter(Driver.id.in_(driver_ids)).all()
    
    if not drivers:
        return {"drivers": []}
    
    driver_dict = {str(d.id): d for d in drivers}
    
    # Get all ratings for these drivers in one query
    ratings_query = db.query(
        DriverRating.driver_id,
        func.avg(DriverRating.rating).label('avg_rating'),
        func.count(DriverRating.id).label('total_ratings')
    ).filter(
        DriverRating.driver_id.in_(driver_ids)
    ).group_by(DriverRating.driver_id).all()
    
    ratings_dict = {
        str(driver_id): {
            "average_rating": round(float(avg_rating or 0.0), 2),
            "total_ratings": int(total_ratings)
        }
        for driver_id, avg_rating, total_ratings in ratings_query
    }
    
    # Build response
    result = []
    for driver_id in driver_ids:
        driver_id_str = str(driver_id)
        driver = driver_dict.get(driver_id_str)
        
        if driver:
            rating_info = ratings_dict.get(driver_id_str, {"average_rating": 0.0, "total_ratings": 0})
            result.append({
                "driver_id": driver_id_str,
                "user_id": str(driver.user_id),
                "vehicle_type": driver.vehicle_type.value if driver.vehicle_type else None,
                "average_rating": rating_info["average_rating"],
                "total_ratings": rating_info["total_ratings"],
                "is_active": driver.is_active,
                "is_verified": driver.is_verified,
                "status": driver.status.value if driver.status else None,
            })
    
    return {"drivers": result}
