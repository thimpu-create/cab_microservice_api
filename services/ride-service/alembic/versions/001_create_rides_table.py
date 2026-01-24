"""create rides table

Revision ID: 001_rides
Revises:
Create Date: 2026-01-24

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "001_rides"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_RIDE_STATUS = postgresql.ENUM(
    "pending", "assigned", "in_progress", "completed", "cancelled", "expired", "rejected",
    name="ridestatusenum",
    create_type=True,
)


def upgrade() -> None:
    _RIDE_STATUS.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "rides",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("request_id", sa.String(255), nullable=False),
        sa.Column("passenger_id", sa.UUID(), nullable=False),
        sa.Column("driver_id", sa.UUID(), nullable=True),
        sa.Column("pickup_lat", sa.Float(), nullable=False),
        sa.Column("pickup_lon", sa.Float(), nullable=False),
        sa.Column("pickup_address", sa.Text(), nullable=True),
        sa.Column("dropoff_lat", sa.Float(), nullable=True),
        sa.Column("dropoff_lon", sa.Float(), nullable=True),
        sa.Column("dropoff_address", sa.Text(), nullable=True),
        sa.Column("vehicle_type", sa.String(20), nullable=True),
        sa.Column("city_code", sa.String(10), nullable=True),
        sa.Column("status", _RIDE_STATUS, nullable=False, server_default="pending"),
        sa.Column("distance_km", sa.Float(), nullable=True),
        sa.Column("duration_minutes", sa.Integer(), nullable=True),
        sa.Column("fare_amount", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_by", sa.String(50), nullable=True),
        sa.Column("cancellation_reason", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_rides_request_id"), "rides", ["request_id"], unique=True)
    op.create_index(op.f("ix_rides_passenger_id"), "rides", ["passenger_id"], unique=False)
    op.create_index(op.f("ix_rides_driver_id"), "rides", ["driver_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_rides_driver_id"), table_name="rides")
    op.drop_index(op.f("ix_rides_passenger_id"), table_name="rides")
    op.drop_index(op.f("ix_rides_request_id"), table_name="rides")
    op.drop_table("rides")
    _RIDE_STATUS.drop(op.get_bind(), checkfirst=True)
