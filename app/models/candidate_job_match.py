from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class CandidateJobMatchRecommendation(StrEnum):
    STRONG_MATCH = "strong_match"
    MATCH = "match"
    PARTIAL_MATCH = "partial_match"
    NOT_RECOMMENDED = "not_recommended"


class CandidateJobMatchConfidence(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class CandidateJobMatch(Base):
    __tablename__ = "candidate_job_matches"

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

    cv_document_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    job_description_document_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    role_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    match_score: Mapped[int] = mapped_column(Integer, nullable=False)

    recommendation: Mapped[CandidateJobMatchRecommendation] = mapped_column(
        Enum(
            CandidateJobMatchRecommendation,
            name="candidate_job_match_recommendation",
        ),
        nullable=False,
    )

    confidence: Mapped[CandidateJobMatchConfidence] = mapped_column(
        Enum(
            CandidateJobMatchConfidence,
            name="candidate_job_match_confidence",
        ),
        nullable=False,
    )

    matched_skills: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    missing_skills: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    risks: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    interview_focus_areas: Mapped[list[str]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
    )
    source_metadata: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
