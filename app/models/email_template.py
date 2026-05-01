from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, Enum, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class EmailTemplateType(StrEnum):
    SHORTLIST = "shortlist"
    REJECTION = "rejection"
    INTERVIEW_INVITE = "interview_invite"
    ASSIGNMENT_REQUEST = "assignment_request"
    ASSIGNMENT_REMINDER = "assignment_reminder"
    FOLLOW_UP = "follow_up"
    OFFER = "offer"
    GENERAL = "general"


class EmailTemplate(Base):
    __tablename__ = "email_templates"

    id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

    template_type: Mapped[EmailTemplateType] = mapped_column(
        Enum(EmailTemplateType, name="email_template_type"),
        nullable=False,
        index=True,
    )

    subject_template: Mapped[str] = mapped_column(String(500), nullable=False)
    body_template: Mapped[str] = mapped_column(Text, nullable=False)

    required_variables: Mapped[list[str]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
    )

    optional_variables: Mapped[list[str]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
    )

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )
