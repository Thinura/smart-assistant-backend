from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Enum, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class AuditEventType(StrEnum):
    APPROVAL_CREATED = "approval.created"
    APPROVAL_APPROVED = "approval.approved"
    APPROVAL_REJECTED = "approval.rejected"
    APPROVAL_EXECUTED = "approval.executed"
    TOOL_EXECUTED = "tool.executed"
    DOCUMENT_UPLOADED = "document.uploaded"
    CANDIDATE_CREATED = "candidate.created"
    CANDIDATE_UPDATED = "candidate.updated"
    AGENT_RUN_COMPLETED = "agent_run.completed"
    APPROVAL_UPDATED = "approval.updated"
    OUTBOX_CREATED = "outbox.created"
    OUTBOX_MARKED_SENT = "outbox.marked_sent"


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    event_type: Mapped[AuditEventType] = mapped_column(
        Enum(AuditEventType, name="audit_event_type"),
        nullable=False,
        index=True,
    )
    actor: Mapped[str | None] = mapped_column(String(255), nullable=True)
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    entity_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    event_metadata: Mapped[dict | None] = mapped_column(
        "metadata",
        JSONB,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
        index=True,
    )
