"""add candidate review audit event

Revision ID: 4c032b7d4c36
Revises: 1ab5f21411f2
Create Date: 2026-04-30 19:14:54.922710

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "4c032b7d4c36"
down_revision: str | Sequence[str] | None = "1ab5f21411f2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'audit_event_type') THEN
                ALTER TYPE audit_event_type
                ADD VALUE IF NOT EXISTS 'CANDIDATE_REVIEW_CREATED';
            END IF;
        END
        $$;
        """
    )


def downgrade() -> None:
    """Downgrade schema."""
    pass
