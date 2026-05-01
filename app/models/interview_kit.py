from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class InterviewKitStatus(StrEnum):
    GENERATED = "generated"
    FAILED = "failed"


class InterviewKit(Base):
    __tablename__ = "interview_kits"

    id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    candidate_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("candidates.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    cv_document_id: Mapped[UUID | None] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    job_description_document_id: Mapped[UUID | None] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    candidate_review_id: Mapped[UUID | None] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("candidate_reviews.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    candidate_job_match_id: Mapped[UUID | None] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("candidate_job_matches.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    role_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    status: Mapped[InterviewKitStatus] = mapped_column(
        Enum(InterviewKitStatus, name="interview_kit_status"),
        nullable=False,
        default=InterviewKitStatus.GENERATED,
    )

    summary: Mapped[str] = mapped_column(Text, nullable=False)
    technical_questions: Mapped[list[dict]] = mapped_column(JSONB, nullable=False, default=list)
    behavioral_questions: Mapped[list[dict]] = mapped_column(JSONB, nullable=False, default=list)
    risk_based_questions: Mapped[list[dict]] = mapped_column(JSONB, nullable=False, default=list)
    evaluation_rubric: Mapped[list[dict]] = mapped_column(JSONB, nullable=False, default=list)
    source_metadata: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
