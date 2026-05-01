from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.audit_log import AuditEventType
from app.models.outbox_message import OutboxMessage, OutboxMessageStatus
from app.services.audit_log_service import AuditLogService
from app.services.email_providers.base import EmailMessage
from app.services.email_providers.factory import EmailProviderFactory


class OutboxSendService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.settings = get_settings()

    def send(self, outbox_message_id: UUID) -> OutboxMessage:
        outbox_message = self.db.get(OutboxMessage, outbox_message_id)

        if outbox_message is None:
            raise ValueError("Outbox message not found")

        if outbox_message.status != OutboxMessageStatus.PENDING:
            raise ValueError("Only pending outbox messages can be sent")

        if not outbox_message.recipient_email:
            raise ValueError("Outbox message does not have a recipient email")

        provider = EmailProviderFactory.create()

        result = provider.send(
            EmailMessage(
                to_email=outbox_message.recipient_email,
                subject=outbox_message.subject,
                body=outbox_message.body,
                from_email=self.settings.email_from_address,
                from_name=self.settings.email_from_name,
            )
        )

        if result.success:
            outbox_message.status = OutboxMessageStatus.SENT
            outbox_message.provider_message_id = result.provider_message_id
            outbox_message.error_message = None
            outbox_message.sent_at = datetime.now(UTC)

            AuditLogService(self.db).record(
                event_type=AuditEventType.OUTBOX_MARKED_SENT,
                entity_type="outbox_message",
                entity_id=str(outbox_message.id),
                actor="system",
                metadata={
                    "status": outbox_message.status.value,
                    "provider_message_id": result.provider_message_id,
                    "email_provider": self.settings.email_provider,
                },
            )
        else:
            outbox_message.status = OutboxMessageStatus.FAILED
            outbox_message.error_message = result.error_message

            AuditLogService(self.db).record(
                event_type=AuditEventType.OUTBOX_SEND_FAILED,
                entity_type="outbox_message",
                entity_id=str(outbox_message.id),
                actor="system",
                metadata={
                    "status": outbox_message.status.value,
                    "error_message": result.error_message,
                    "email_provider": self.settings.email_provider,
                },
            )

        self.db.commit()
        self.db.refresh(outbox_message)

        return outbox_message
