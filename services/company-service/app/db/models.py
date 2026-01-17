import uuid
from sqlalchemy import (
    Column, String, Boolean, DateTime, Enum, JSON, Text, ForeignKey, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .base import Base
import enum


class CompanyStatus(enum.Enum):
    active = "active"
    suspended = "suspended"
    pending_verification = "pending_verification"
    closed = "closed"


class CompanyType(enum.Enum):
    sole_proprietor = "sole_proprietor"
    partnership = "partnership"
    llc = "llc"
    corporation = "corporation"


class OperatingRegion(enum.Enum):
    usa = "USA"
    canada = "CANADA"
    international = "INTERNATIONAL"



class CabCompany(Base):
    __tablename__ = "cab_companies"

    # ---- Identity ----
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_user_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    company_name = Column(String(255), nullable=False)
    legal_name = Column(String(255), nullable=True)
    company_type = Column(Enum(CompanyType), nullable=False)

    status = Column(Enum(CompanyStatus), default=CompanyStatus.pending_verification)

    # ---- Region & Locale ----
    operating_region = Column(Enum(OperatingRegion), nullable=False)
    country = Column(String(50), nullable=False)  # USA / Canada
    state_province = Column(String(100), nullable=False)
    city = Column(String(100), nullable=False)

    timezone = Column(String(50), nullable=False)  # e.g. America/New_York
    currency = Column(String(10), nullable=False, default="USD")

    # ---- Address ----
    address_line1 = Column(String(255), nullable=False)
    address_line2 = Column(String(255), nullable=True)
    postal_code = Column(String(20), nullable=False)

    # ---- Contact ----
    business_email = Column(String(255), nullable=False)
    business_phone = Column(String(30), nullable=False)
    support_phone = Column(String(30), nullable=True)
    support_email = Column(String(255), nullable=True)

    website_url = Column(String(255), nullable=True)

    # ---- Compliance & Licensing ----
    us_dot_number = Column(String(50), nullable=True)   # USA
    mc_number = Column(String(50), nullable=True)       # USA interstate
    cvor_number = Column(String(50), nullable=True)     # Canada

    business_license_number = Column(String(100), nullable=True)
    license_expiry_date = Column(DateTime, nullable=True)

    insurance_policy_number = Column(String(100), nullable=True)
    insurance_expiry_date = Column(DateTime, nullable=True)
    insurance_provider = Column(String(255), nullable=True)

    # ---- Tax & Payments ----
    tax_id = Column(String(100), nullable=True)  # EIN (US) / BN (Canada)
    tax_percentage = Column(String(10), nullable=True)

    payout_bank_details = Column(JSON, nullable=True)  
    # Example:
    # {
    #   "bank_name": "",
    #   "account_last4": "",
    #   "routing_number": ""
    # }

    # ---- Operations ----
    fleet_size = Column(String(20), nullable=True)
    service_areas = Column(JSON, nullable=True)
    # Example: ["New York City", "Newark", "Jersey City"]

    operating_hours = Column(JSON, nullable=True)
    # Example:
    # {
    #   "mon_fri": "06:00-23:00",
    #   "sat_sun": "24hrs"
    # }

    # ---- Metadata ----
    notes = Column(Text, nullable=True)

    is_verified = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class UserCompanyRole(enum.Enum):
    """Roles a user can have within a company."""
    owner = "owner"
    admin = "admin"
    manager = "manager"
    dispatcher = "dispatcher"
    support = "support"
    driver = "driver"
    accountant = "accountant"


class CompanyUser(Base):
    """
    Association table (follower/following pattern) linking users to companies.
    Many-to-many relationship: Users can belong to multiple companies, 
    Companies can have multiple users.
    
    This follows the standard junction table pattern similar to:
    - followers/following relationships in social media
    - user-group associations
    - many-to-many relationships with additional attributes
    """
    __tablename__ = "company_users"
    
    # ---- Primary Key ----
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # ---- Foreign Keys (Junction Table Pattern) ----
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)  # Links to auth-service users.uuid
    company_id = Column(
        UUID(as_uuid=True),
        ForeignKey("cab_companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # ---- Role & Status (Additional attributes on the relationship) ----
    role = Column(Enum(UserCompanyRole), nullable=False, default=UserCompanyRole.driver)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    
    # ---- Permissions (Additional attributes) ----
    can_manage_drivers = Column(Boolean, default=False)
    can_manage_rides = Column(Boolean, default=False)
    can_view_reports = Column(Boolean, default=False)
    can_manage_payments = Column(Boolean, default=False)
    
    # ---- Metadata ----
    joined_at = Column(DateTime(timezone=True), server_default=func.now())
    left_at = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # ---- Constraints (Prevent duplicate associations) ----
    __table_args__ = (
        UniqueConstraint('user_id', 'company_id', name='uq_user_company'),
    )
    
    # ---- Relationships ----
    company = relationship("CabCompany", backref="associated_users")