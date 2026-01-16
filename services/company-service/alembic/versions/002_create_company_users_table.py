"""create company_users table

Revision ID: 002_create_company_users
Revises: 5a295a294883
Create Date: 2026-01-16 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '002_create_company_users'
down_revision: Union[str, None] = '5a295a294883'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create company_users table."""
    # Check if enum exists
    conn = op.get_bind()
    result = conn.execute(sa.text("SELECT 1 FROM pg_type WHERE typname = 'usercompanyrole'"))
    if result.fetchone() is None:
        usercompanyrole_enum = postgresql.ENUM(
            'owner', 'admin', 'manager', 'dispatcher', 'support', 'driver', 'accountant',
            name='usercompanyrole',
            create_type=True
        )
        usercompanyrole_enum.create(conn, checkfirst=False)
    
    op.create_table(
        'company_users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('role', postgresql.ENUM('owner', 'admin', 'manager', 'dispatcher', 'support', 'driver', 'accountant', name='usercompanyrole'), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('is_verified', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('can_manage_drivers', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('can_manage_rides', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('can_view_reports', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('can_manage_payments', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('joined_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('left_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['cab_companies.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'company_id', name='uq_user_company')
    )
    
    # Create indexes
    op.create_index(op.f('ix_company_users_user_id'), 'company_users', ['user_id'], unique=False)
    op.create_index(op.f('ix_company_users_company_id'), 'company_users', ['company_id'], unique=False)


def downgrade() -> None:
    """Drop company_users table."""
    op.drop_index(op.f('ix_company_users_company_id'), table_name='company_users')
    op.drop_index(op.f('ix_company_users_user_id'), table_name='company_users')
    op.drop_table('company_users')
    op.execute('DROP TYPE IF EXISTS usercompanyrole')
