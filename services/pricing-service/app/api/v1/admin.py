"""
Admin endpoints for managing pricing profiles and configurations.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.db.session import get_db
from app.db.models import PricingProfile, SurgeConfig, VehicleType
from app.schemas.pricing import (
    PricingProfileCreate, PricingProfileResponse,
    SurgeConfigUpdate, SurgeConfigResponse
)
from app.core.security import get_current_user_role, verify_admin_role

router = APIRouter(prefix="/admin/pricing", tags=["Pricing Admin"])


@router.get("/profiles", response_model=List[PricingProfileResponse], status_code=status.HTTP_200_OK)
async def list_pricing_profiles(
    city_code: str = None,
    vehicle_type: VehicleType = None,
    db: Session = Depends(get_db),
    role: str = Depends(get_current_user_role)
):
    """List platform pricing profiles (admin only - company_id = NULL)."""
    if not verify_admin_role(role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    # Only show platform pricing (company_id = NULL)
    query = db.query(PricingProfile).filter(PricingProfile.company_id.is_(None))
    
    if city_code:
        query = query.filter(PricingProfile.city_code == city_code)
    if vehicle_type:
        query = query.filter(PricingProfile.vehicle_type == vehicle_type)
    
    profiles = query.all()
    return profiles


@router.post("/profiles", response_model=PricingProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_pricing_profile(
    profile: PricingProfileCreate,
    db: Session = Depends(get_db),
    role: str = Depends(get_current_user_role)
):
    """Create pricing profile (admin only)."""
    if not verify_admin_role(role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    # Admin creates platform pricing (company_id = NULL)
    new_profile = PricingProfile(
        company_id=None,  # Platform pricing for independent drivers
        city_code=profile.city_code,
        state_code=profile.state_code,
        vehicle_type=profile.vehicle_type,
        base_fare=profile.base_fare,
        per_km_rate=profile.per_km_rate,
        per_minute_rate=profile.per_minute_rate,
        minimum_fare=profile.minimum_fare,
        effective_from=profile.effective_from,
        effective_to=profile.effective_to,
        is_active=True
    )
    
    db.add(new_profile)
    db.commit()
    db.refresh(new_profile)
    
    return new_profile


@router.put("/profiles/{profile_id}", response_model=PricingProfileResponse, status_code=status.HTTP_200_OK)
async def update_pricing_profile(
    profile_id: UUID,
    profile: PricingProfileCreate,
    db: Session = Depends(get_db),
    role: str = Depends(get_current_user_role)
):
    """Update pricing profile (admin only)."""
    if not verify_admin_role(role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    existing = db.query(PricingProfile).filter(PricingProfile.id == profile_id).first()
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pricing profile not found"
        )
    
    existing.city_code = profile.city_code
    existing.state_code = profile.state_code
    existing.vehicle_type = profile.vehicle_type
    existing.base_fare = profile.base_fare
    existing.per_km_rate = profile.per_km_rate
    existing.per_minute_rate = profile.per_minute_rate
    existing.minimum_fare = profile.minimum_fare
    existing.effective_from = profile.effective_from
    existing.effective_to = profile.effective_to
    
    db.commit()
    db.refresh(existing)
    
    return existing


@router.get("/surge-config", response_model=List[SurgeConfigResponse], status_code=status.HTTP_200_OK)
async def list_surge_configs(
    db: Session = Depends(get_db),
    role: str = Depends(get_current_user_role)
):
    """List platform surge configurations (admin only - company_id = NULL)."""
    if not verify_admin_role(role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    # Only show platform surge configs
    configs = db.query(SurgeConfig).filter(SurgeConfig.company_id.is_(None)).all()
    return configs


@router.put("/surge-config/{vehicle_type}", response_model=SurgeConfigResponse, status_code=status.HTTP_200_OK)
async def update_surge_config(
    vehicle_type: VehicleType,
    config: SurgeConfigUpdate,
    db: Session = Depends(get_db),
    role: str = Depends(get_current_user_role)
):
    """Update surge configuration (admin only)."""
    if not verify_admin_role(role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    # Only allow updating platform surge config (company_id = NULL)
    existing = db.query(SurgeConfig).filter(
        SurgeConfig.vehicle_type == vehicle_type,
        SurgeConfig.company_id.is_(None)  # Only platform surge (use .is_(None) for NULL check)
    ).first()
    
    if existing:
        if config.base_demand_threshold is not None:
            existing.base_demand_threshold = config.base_demand_threshold
        if config.max_surge_multiplier is not None:
            existing.max_surge_multiplier = config.max_surge_multiplier
        if config.surge_increment is not None:
            existing.surge_increment = config.surge_increment
    else:
        from app.core.config import settings
        # Create platform surge config (company_id = NULL)
        existing = SurgeConfig(
            company_id=None,  # Platform surge config
            vehicle_type=vehicle_type,
            base_demand_threshold=config.base_demand_threshold or settings.DEFAULT_BASE_DEMAND_THRESHOLD,
            max_surge_multiplier=config.max_surge_multiplier or settings.DEFAULT_MAX_SURGE,
            surge_increment=config.surge_increment or settings.DEFAULT_SURGE_INCREMENT,
            is_active=True
        )
        db.add(existing)
    
    db.commit()
    db.refresh(existing)
    
    return existing
