"""create drivers table

Revision ID: 001_create_drivers
Revises: 
Create Date: 2025-01-16 11:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_create_drivers'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create enum type for driver status (only if it doesn't exist)
    conn = op.get_bind()
    result = conn.execute(sa.text("SELECT 1 FROM pg_type WHERE typname = 'driverstatus'"))
    enum_exists = result.fetchone() is not None
    
    if not enum_exists:
        op.execute("CREATE TYPE driverstatus AS ENUM ('active', 'inactive', 'suspended', 'pending_verification')")
    
    # Reference the enum type (it exists now, either created above or already in DB)
    driverstatus_enum = postgresql.ENUM(
        'active', 'inactive', 'suspended', 'pending_verification',
        name='driverstatus',
        create_type=False  # Don't try to create, it already exists
    )
    
    # Create drivers table
    op.create_table('drivers',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('license_number', sa.String(length=100), nullable=True),
        sa.Column('license_expiry_date', sa.DateTime(), nullable=True),
        sa.Column('license_state_province', sa.String(length=100), nullable=True),
        sa.Column('vehicle_make', sa.String(length=100), nullable=True),
        sa.Column('vehicle_model', sa.String(length=100), nullable=True),
        sa.Column('vehicle_year', sa.Integer(), nullable=True),
        sa.Column('vehicle_color', sa.String(length=50), nullable=True),
        sa.Column('vehicle_plate_number', sa.String(length=50), nullable=True),
        sa.Column('status', driverstatus_enum, nullable=True),
        sa.Column('is_verified', sa.Boolean(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_drivers_user_id'), 'drivers', ['user_id'], unique=False)
    op.create_index(op.f('ix_drivers_company_id'), 'drivers', ['company_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_drivers_company_id'), table_name='drivers')
    op.drop_index(op.f('ix_drivers_user_id'), table_name='drivers')
    op.drop_table('drivers')
    op.execute('DROP TYPE IF EXISTS driverstatus')
