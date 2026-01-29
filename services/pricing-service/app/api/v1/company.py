"""
Company endpoints for managing company-specific pricing (VendorAdmin only).
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.db.session import get_db
from app.db.models import PricingProfile, PeakHours, SurgeConfig, RegulatoryCap, VehicleType
from app.schemas.pricing import (
    PricingProfileCreate, PricingProfileResponse,
    SurgeConfigUpdate, SurgeConfigResponse
)
from app.core.security import get_current_user_id, get_current_user_role
from app.core.company_client import get_user_company_id

router = APIRouter(prefix="/company/pricing", tags=["Company Pricing"])


async def get_current_company_id(
    user_id: UUID = Depends(get_current_user_id),
    role: str = Depends(get_current_user_role)
) -> UUID:
    """
    Dependency to get company_id for VendorAdmin.
    Gets company where user is owner (owner_user_id = user_id).
    """
    if role != "VendorAdmin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only VendorAdmin can access company pricing"
        )
    
    # Get company_id from company-service
    # For now, we'll need to query company-service or add an endpoint
    # Alternative: Get from CompanyUser where user is owner
    company_id = await get_user_company_id(user_id)
    
    if not company_id:
        # Try alternative: Query company-service for companies owned by user
        # This would require an endpoint like GET /companies/owned-by/{user_id}
        # For now, raise error - company_id must be available
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found for this user. Please ensure you own a company."
        )
    
    return company_id


# ==================== Pricing Profiles ====================

@router.get("/profiles", response_model=List[PricingProfileResponse], status_code=status.HTTP_200_OK)
async def list_company_pricing_profiles(
    city_code: Optional[str] = None,
    vehicle_type: Optional[VehicleType] = None,
    db: Session = Depends(get_db),
    company_id: UUID = Depends(get_current_company_id)
):
    """List company pricing profiles (VendorAdmin only)."""
    query = db.query(PricingProfile).filter(
        PricingProfile.company_id == company_id  # Only this company's pricing
    )
    
    if city_code:
        query = query.filter(PricingProfile.city_code == city_code)
    if vehicle_type:
        query = query.filter(PricingProfile.vehicle_type == vehicle_type)
    
    profiles = query.all()
    return profiles


@router.post("/profiles", response_model=PricingProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_company_pricing_profile(
    profile: PricingProfileCreate,
    db: Session = Depends(get_db),
    company_id: UUID = Depends(get_current_company_id)
):
    """Create company pricing profile (VendorAdmin only)."""
    new_profile = PricingProfile(
        company_id=company_id,  # Company-specific pricing
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
async def update_company_pricing_profile(
    profile_id: UUID,
    profile: PricingProfileCreate,
    db: Session = Depends(get_db),
    company_id: UUID = Depends(get_current_company_id)
):
    """Update company pricing profile (VendorAdmin only)."""
    existing = db.query(PricingProfile).filter(
        PricingProfile.id == profile_id,
        PricingProfile.company_id == company_id  # Only their company's pricing
    ).first()
    
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company pricing profile not found"
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


@router.delete("/profiles/{profile_id}", status_code=status.HTTP_200_OK)
async def delete_company_pricing_profile(
    profile_id: UUID,
    db: Session = Depends(get_db),
    company_id: UUID = Depends(get_current_company_id)
):
    """Delete (deactivate) company pricing profile (VendorAdmin only)."""
    existing = db.query(PricingProfile).filter(
        PricingProfile.id == profile_id,
        PricingProfile.company_id == company_id
    ).first()
    
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company pricing profile not found"
        )
    
    existing.is_active = False
    db.commit()
    
    return {"message": "Pricing profile deactivated successfully"}


# ==================== Surge Config ====================

@router.get("/surge-config", response_model=List[SurgeConfigResponse], status_code=status.HTTP_200_OK)
async def list_company_surge_configs(
    db: Session = Depends(get_db),
    company_id: UUID = Depends(get_current_company_id)
):
    """List company surge configurations (VendorAdmin only)."""
    configs = db.query(SurgeConfig).filter(
        SurgeConfig.company_id == company_id  # Only this company's surge config
    ).all()
    return configs


@router.put("/surge-config/{vehicle_type}", response_model=SurgeConfigResponse, status_code=status.HTTP_200_OK)
async def update_company_surge_config(
    vehicle_type: VehicleType,
    config: SurgeConfigUpdate,
    db: Session = Depends(get_db),
    company_id: UUID = Depends(get_current_company_id)
):
    """Update company surge configuration (VendorAdmin only)."""
    existing = db.query(SurgeConfig).filter(
        SurgeConfig.vehicle_type == vehicle_type,
        SurgeConfig.company_id == company_id  # Only their company's surge config
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
        # Create company surge config
        existing = SurgeConfig(
            company_id=company_id,  # Company-specific surge config
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
