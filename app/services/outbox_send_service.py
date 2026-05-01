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

        if outbox_message.status not in {
            OutboxMessageStatus.PENDING,
            OutboxMessageStatus.FAILED,
        }:
            raise ValueError("Only pending or failed outbox messages can be sent")

        if not outbox_message.recipient_email:
            raise ValueError("Outbox message does not have a recipient email")

        outbox_message.error_message = None

        self.db.flush()
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

    def send_pending(
        self,
        *,
        limit: int = 50,
        include_failed: bool = False,
    ) -> dict:
        statuses = [OutboxMessageStatus.PENDING]

        if include_failed:
            statuses.append(OutboxMessageStatus.FAILED)

        messages = (
            self.db.query(OutboxMessage)
            .filter(OutboxMessage.status.in_(statuses))
            .order_by(OutboxMessage.created_at.asc())
            .limit(limit)
            .all()
        )

        results = []

        for message in messages:
            try:
                sent_message = self.send(message.id)

                results.append(
                    {
                        "id": str(sent_message.id),
                        "status": sent_message.status.value,
                        "provider_message_id": sent_message.provider_message_id,
                        "error_message": sent_message.error_message,
                    }
                )
            except ValueError as exc:
                results.append(
                    {
                        "id": str(message.id),
                        "status": message.status.value,
                        "provider_message_id": message.provider_message_id,
                        "error_message": str(exc),
                    }
                )

        sent_count = sum(1 for item in results if item["status"] == "sent")
        failed_count = sum(1 for item in results if item["status"] == "failed")

        return {
            "total": len(results),
            "sent_count": sent_count,
            "failed_count": failed_count,
            "results": results,
        }

    def get_summary(self) -> dict:
        pending_count = (
            self.db.query(OutboxMessage)
            .filter(OutboxMessage.status == OutboxMessageStatus.PENDING)
            .count()
        )

        sent_count = (
            self.db.query(OutboxMessage)
            .filter(OutboxMessage.status == OutboxMessageStatus.SENT)
            .count()
        )

        failed_count = (
            self.db.query(OutboxMessage)
            .filter(OutboxMessage.status == OutboxMessageStatus.FAILED)
            .count()
        )

        return {
            "pending_count": pending_count,
            "sent_count": sent_count,
            "failed_count": failed_count,
            "total_count": pending_count + sent_count + failed_count,
        }
