from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.audit_log import AuditEventType
from app.models.outbox_message import OutboxMessage, OutboxMessageStatus
from app.services.audit_log_service import AuditLogService


def _parse_optional_uuid(value: str | None) -> UUID | None:
    if not value:
        return None

    try:
        return UUID(value)
    except ValueError:
        return None


class OutboxService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_from_email_approval(
        self,
        *,
        approval_request_id: UUID,
        action_payload: dict,
    ) -> OutboxMessage:
        candidate_id_value = action_payload.get("candidate_id")
        candidate_id = _parse_optional_uuid(candidate_id_value)
        outbox_message = OutboxMessage(
            approval_request_id=approval_request_id,
            candidate_id=candidate_id,
            recipient_email=action_payload.get("candidate_email"),
            subject=action_payload.get("subject"),
            body=action_payload.get("draft_body") or "",
            status=OutboxMessageStatus.PENDING,
        )

        self.db.add(outbox_message)
        self.db.flush()

        AuditLogService(self.db).record(
            event_type=AuditEventType.OUTBOX_CREATED,
            entity_type="outbox_message",
            entity_id=str(outbox_message.id),
            actor="system",
            metadata={
                "approval_request_id": str(approval_request_id),
                "candidate_id": str(candidate_id) if candidate_id else None,
                "recipient_email": outbox_message.recipient_email,
                "subject": outbox_message.subject,
                "status": outbox_message.status.value,
            },
        )

        return outbox_message

    def mark_sent(
        self,
        *,
        outbox_message: OutboxMessage,
        provider_message_id: str | None = None,
    ) -> OutboxMessage:
        outbox_message.status = OutboxMessageStatus.SENT
        outbox_message.provider_message_id = provider_message_id
        outbox_message.error_message = None
        outbox_message.sent_at = datetime.now(UTC)

        self.db.flush()

        AuditLogService(self.db).record(
            event_type=AuditEventType.OUTBOX_MARKED_SENT,
            entity_type="outbox_message",
            entity_id=str(outbox_message.id),
            actor="system",
            metadata={
                "provider_message_id": provider_message_id,
                "status": outbox_message.status.value,
            },
        )

        return outbox_message
