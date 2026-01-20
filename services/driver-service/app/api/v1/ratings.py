from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from uuid import UUID
from typing import List, Optional

from app.db.session import get_db
from app.db.models import Driver, DriverRating
from app.schemas.rating import DriverRatingCreate, DriverRatingResponse, DriverRatingStats
from app.core.security import get_current_user_id

router = APIRouter(prefix="/ratings", tags=["Driver Ratings"])


@router.post("/", response_model=DriverRatingResponse, status_code=status.HTTP_201_CREATED)
async def create_rating(
    rating_data: DriverRatingCreate,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Create a rating for a driver. Only passengers can rate drivers.
    """
    # Verify driver exists
    driver = db.query(Driver).filter(Driver.id == rating_data.driver_id).first()
    if not driver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Driver not found"
        )
    
    # Verify passenger_id matches authenticated user
    if rating_data.passenger_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only create ratings for yourself"
        )
    
    # Check if passenger already rated this driver for this ride (if ride_id provided)
    if rating_data.ride_id:
        existing = db.query(DriverRating).filter(
            DriverRating.driver_id == rating_data.driver_id,
            DriverRating.passenger_id == rating_data.passenger_id,
            DriverRating.ride_id == rating_data.ride_id
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="You have already rated this driver for this ride"
            )
    
    # Create rating
    rating = DriverRating(
        driver_id=rating_data.driver_id,
        passenger_id=rating_data.passenger_id,
        ride_id=rating_data.ride_id,
        rating=rating_data.rating,
        comment=rating_data.comment,
        punctuality_rating=rating_data.punctuality_rating,
        driving_rating=rating_data.driving_rating,
        vehicle_condition_rating=rating_data.vehicle_condition_rating,
        communication_rating=rating_data.communication_rating,
    )
    
    db.add(rating)
    db.commit()
    db.refresh(rating)
    
    return rating


@router.get("/driver/{driver_id}/stats", response_model=DriverRatingStats)
async def get_driver_rating_stats(
    driver_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get rating statistics for a driver.
    """
    # Verify driver exists
    driver = db.query(Driver).filter(Driver.id == driver_id).first()
    if not driver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Driver not found"
        )
    
    # Get all ratings for this driver
    ratings = db.query(DriverRating).filter(DriverRating.driver_id == driver_id).all()
    
    if not ratings:
        return DriverRatingStats(
            driver_id=driver_id,
            average_rating=0.0,
            total_ratings=0,
            rating_distribution={1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        )
    
    # Calculate average
    total_ratings = len(ratings)
    average_rating = sum(r.rating for r in ratings) / total_ratings
    
    # Rating distribution
    distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    for rating in ratings:
        rating_int = int(rating.rating)
        if 1 <= rating_int <= 5:
            distribution[rating_int] = distribution.get(rating_int, 0) + 1
    
    # Calculate category averages
    punctuality_ratings = [r.punctuality_rating for r in ratings if r.punctuality_rating]
    driving_ratings = [r.driving_rating for r in ratings if r.driving_rating]
    vehicle_ratings = [r.vehicle_condition_rating for r in ratings if r.vehicle_condition_rating]
    communication_ratings = [r.communication_rating for r in ratings if r.communication_rating]
    
    return DriverRatingStats(
        driver_id=driver_id,
        average_rating=round(average_rating, 2),
        total_ratings=total_ratings,
        rating_distribution=distribution,
        average_punctuality=round(sum(punctuality_ratings) / len(punctuality_ratings), 2) if punctuality_ratings else None,
        average_driving=round(sum(driving_ratings) / len(driving_ratings), 2) if driving_ratings else None,
        average_vehicle_condition=round(sum(vehicle_ratings) / len(vehicle_ratings), 2) if vehicle_ratings else None,
        average_communication=round(sum(communication_ratings) / len(communication_ratings), 2) if communication_ratings else None,
    )


@router.get("/driver/{driver_id}/average", response_model=dict)
async def get_driver_average_rating(
    driver_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get average rating for a driver (quick endpoint for matching algorithm).
    Returns 0.0 if no ratings exist.
    """
    result = db.query(func.avg(DriverRating.rating)).filter(
        DriverRating.driver_id == driver_id
    ).scalar()
    
    return {
        "driver_id": str(driver_id),
        "average_rating": round(float(result or 0.0), 2),
        "total_ratings": db.query(DriverRating).filter(DriverRating.driver_id == driver_id).count()
    }


@router.get("/driver/{driver_id}", response_model=List[DriverRatingResponse])
async def get_driver_ratings(
    driver_id: UUID,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    Get all ratings for a driver with pagination.
    """
    ratings = db.query(DriverRating).filter(
        DriverRating.driver_id == driver_id
    ).order_by(DriverRating.created_at.desc()).offset(skip).limit(limit).all()
    
    return ratings
