"""add approval updated audit event

Revision ID: 25144525b9a6
Revises: ef74cd89bb17
Create Date: 2026-04-28 12:00:53.712949

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "25144525b9a6"
down_revision: str | Sequence[str] | None = "ef74cd89bb17"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TYPE audit_event_type ADD VALUE IF NOT EXISTS 'APPROVAL_UPDATED'")


def downgrade() -> None:
    """Downgrade schema."""
    pass
