"""add approval request updated audit event

Revision ID: 21a5fa405085
Revises: 57b901b473c5
Create Date: 2026-05-02 03:18:34.897954

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "21a5fa405085"
down_revision: str | Sequence[str] | None = "57b901b473c5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'audit_event_type') THEN
                ALTER TYPE audit_event_type
                ADD VALUE IF NOT EXISTS 'APPROVAL_REQUEST_UPDATED';
            END IF;
        END
        $$;
        """
    )


def downgrade() -> None:
    """Downgrade schema."""
    pass
