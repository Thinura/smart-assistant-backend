"""add failed outbox status

Revision ID: 4a79d41a8d14
Revises: 146e0317e533
Create Date: 2026-05-02 02:07:27.091733

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "4a79d41a8d14"
down_revision: str | Sequence[str] | None = "146e0317e533"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'outbox_message_status') THEN
                ALTER TYPE outbox_message_status ADD VALUE IF NOT EXISTS 'FAILED';
            END IF;

            IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'audit_event_type') THEN
                ALTER TYPE audit_event_type ADD VALUE IF NOT EXISTS 'OUTBOX_SEND_FAILED';
            END IF;
        END
        $$;
        """
    )


def downgrade() -> None:
    """Downgrade schema."""
    pass
