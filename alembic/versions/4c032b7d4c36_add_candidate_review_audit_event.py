"""add candidate review audit event

Revision ID: 4c032b7d4c36
Revises: 1ab5f21411f2
Create Date: 2026-04-30 19:14:54.922710

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4c032b7d4c36'
down_revision: Union[str, Sequence[str], None] = '1ab5f21411f2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "ALTER TYPE audit_event_type "
        "ADD VALUE IF NOT EXISTS 'CANDIDATE_REVIEW_CREATED'"
    )


def downgrade() -> None:
    """Downgrade schema."""
    pass
