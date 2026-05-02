"""create candidate workflows table

Revision ID: 21f6767f67f8
Revises: 21a5fa405085
Create Date: 2026-05-02 13:24:07.770063

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "21f6767f67f8"
down_revision: str | Sequence[str] | None = "21a5fa405085"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:

    candidate_workflow_type = postgresql.ENUM(
        "INTERVIEW_PREPARATION",
        name="candidate_workflow_type",
    )

    candidate_workflow_status = postgresql.ENUM(
        "COMPLETED",
        "FAILED",
        "PARTIAL",
        name="candidate_workflow_status",
    )

    candidate_workflow_type.create(op.get_bind(), checkfirst=True)

    candidate_workflow_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "candidate_workflows",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("candidate_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("agent_run_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("workflow_type", candidate_workflow_type, nullable=False),
        sa.Column("status", candidate_workflow_status, nullable=False),
        sa.Column("role_name", sa.String(length=255), nullable=True),
        sa.Column("candidate_review_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("candidate_job_match_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("interview_kit_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("approval_request_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("score", sa.Integer(), nullable=True),
        sa.Column("recommendation", sa.String(length=100), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("workflow_metadata", postgresql.JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["agent_run_id"], ["agent_runs.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(
            ["approval_request_id"], ["approval_requests.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(["candidate_id"], ["candidates.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["candidate_job_match_id"], ["candidate_job_matches.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["candidate_review_id"], ["candidate_reviews.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(["interview_kit_id"], ["interview_kits.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_candidate_workflows_candidate_id",
        "candidate_workflows",
        ["candidate_id"],
    )

    op.create_index(
        "ix_candidate_workflows_agent_run_id",
        "candidate_workflows",
        ["agent_run_id"],
    )


def downgrade() -> None:

    op.drop_index("ix_candidate_workflows_agent_run_id", table_name="candidate_workflows")

    op.drop_index("ix_candidate_workflows_candidate_id", table_name="candidate_workflows")

    op.drop_table("candidate_workflows")

    postgresql.ENUM(name="candidate_workflow_status").drop(op.get_bind(), checkfirst=True)

    postgresql.ENUM(name="candidate_workflow_type").drop(op.get_bind(), checkfirst=True)
