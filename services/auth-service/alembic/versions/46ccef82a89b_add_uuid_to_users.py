"""add uuid to users

Revision ID: 46ccef82a89b
Revises: 5243bcea27dc
Create Date: 2025-12-22 17:08:07.164281

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '46ccef82a89b'
down_revision: Union[str, Sequence[str], None] = '5243bcea27dc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "uuid",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        )
    )

    # 2️⃣ Backfill existing rows
    op.execute(
        "UPDATE users SET uuid = gen_random_uuid() WHERE uuid IS NULL"
    )

    # 3️⃣ Enforce NOT NULL
    op.alter_column("users", "uuid", nullable=False)

    # 4️⃣ Add unique index
    op.create_index(
        "ix_users_uuid",
        "users",
        ["uuid"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_users_uuid", table_name="users")
    op.drop_column("users", "uuid")
