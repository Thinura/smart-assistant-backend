"""enable pgvector extension

Revision ID: 5c008ad37c17
Revises: 75df4fa48ad8
Create Date: 2026-04-26 15:59:47.583026

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "5c008ad37c17"
down_revision: str | Sequence[str] | None = "75df4fa48ad8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")


def downgrade() -> None:
    op.execute("DROP EXTENSION IF EXISTS vector")
