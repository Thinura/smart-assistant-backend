from datetime import UTC, datetime
from enum import StrEnum
from uuid import uuid4

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class CandidateWorkflowType(StrEnum):
    INTERVIEW_PREPARATION = "interview_preparation"


class CandidateWorkflowStatus(StrEnum):
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


class CandidateWorkflow(Base):
    __tablename__ = "candidate_workflows"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    candidate_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("candidates.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    agent_run_id: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agent_runs.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    workflow_type: Mapped[CandidateWorkflowType] = mapped_column(
        Enum(CandidateWorkflowType, name="candidate_workflow_type"),
        nullable=False,
    )

    status: Mapped[CandidateWorkflowStatus] = mapped_column(
        Enum(CandidateWorkflowStatus, name="candidate_workflow_status"),
        nullable=False,
    )

    role_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    candidate_review_id: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("candidate_reviews.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    candidate_job_match_id: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("candidate_job_matches.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    interview_kit_id: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("interview_kits.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    approval_request_id: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("approval_requests.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    recommendation: Mapped[str | None] = mapped_column(String(100), nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    workflow_metadata: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
