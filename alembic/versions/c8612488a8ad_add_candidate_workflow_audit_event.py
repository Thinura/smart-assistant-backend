"""add candidate workflow audit event

Revision ID: c8612488a8ad
Revises: 21f6767f67f8
Create Date: 2026-05-02 14:01:21.128033

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c8612488a8ad"
down_revision: str | Sequence[str] | None = "21f6767f67f8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'audit_event_type') THEN
                ALTER TYPE audit_event_type ADD VALUE IF NOT EXISTS 'CANDIDATE_WORKFLOW_CREATED';
            END IF;
        END
        $$;
        """
    )


def downgrade() -> None:
    """Downgrade schema."""
    pass
