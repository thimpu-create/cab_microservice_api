"""add company_id for company-based pricing

Revision ID: 002_company_pricing
Revises: d1d6c58173a9
Create Date: 2026-01-24

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '002_company_pricing'
down_revision: Union[str, Sequence[str], None] = 'd1d6c58173a9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # pricing_profiles: add company_id
    op.add_column('pricing_profiles', sa.Column('company_id', sa.UUID(), nullable=True))
    op.create_index(op.f('ix_pricing_profiles_company_id'), 'pricing_profiles', ['company_id'], unique=False)

    # peak_hours: add company_id
    op.add_column('peak_hours', sa.Column('company_id', sa.UUID(), nullable=True))
    op.create_index(op.f('ix_peak_hours_company_id'), 'peak_hours', ['company_id'], unique=False)

    # surge_configs: add company_id, drop old unique on vehicle_type, add new unique on (company_id, vehicle_type)
    op.add_column('surge_configs', sa.Column('company_id', sa.UUID(), nullable=True))
    op.create_index(op.f('ix_surge_configs_company_id'), 'surge_configs', ['company_id'], unique=False)
    op.drop_index('ix_surge_configs_vehicle_type', table_name='surge_configs')
    op.create_unique_constraint('uq_surge_config_company_vehicle', 'surge_configs', ['company_id', 'vehicle_type'])

    # regulatory_caps: add company_id
    op.add_column('regulatory_caps', sa.Column('company_id', sa.UUID(), nullable=True))
    op.create_index(op.f('ix_regulatory_caps_company_id'), 'regulatory_caps', ['company_id'], unique=False)

    # pricing_calculations: add driver_id, company_id
    op.add_column('pricing_calculations', sa.Column('driver_id', sa.UUID(), nullable=True))
    op.add_column('pricing_calculations', sa.Column('company_id', sa.UUID(), nullable=True))
    op.create_index(op.f('ix_pricing_calculations_driver_id'), 'pricing_calculations', ['driver_id'], unique=False)
    op.create_index(op.f('ix_pricing_calculations_company_id'), 'pricing_calculations', ['company_id'], unique=False)


def downgrade() -> None:
    # pricing_calculations
    op.drop_index(op.f('ix_pricing_calculations_company_id'), table_name='pricing_calculations')
    op.drop_index(op.f('ix_pricing_calculations_driver_id'), table_name='pricing_calculations')
    op.drop_column('pricing_calculations', 'company_id')
    op.drop_column('pricing_calculations', 'driver_id')

    # regulatory_caps
    op.drop_index(op.f('ix_regulatory_caps_company_id'), table_name='regulatory_caps')
    op.drop_column('regulatory_caps', 'company_id')

    # surge_configs
    op.drop_constraint('uq_surge_config_company_vehicle', 'surge_configs', type_='unique')
    op.create_index('ix_surge_configs_vehicle_type', 'surge_configs', ['vehicle_type'], unique=True)
    op.drop_index(op.f('ix_surge_configs_company_id'), table_name='surge_configs')
    op.drop_column('surge_configs', 'company_id')

    # peak_hours
    op.drop_index(op.f('ix_peak_hours_company_id'), table_name='peak_hours')
    op.drop_column('peak_hours', 'company_id')

    # pricing_profiles
    op.drop_index(op.f('ix_pricing_profiles_company_id'), table_name='pricing_profiles')
    op.drop_column('pricing_profiles', 'company_id')
