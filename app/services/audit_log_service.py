from typing import Any

from sqlalchemy.orm import Session

from app.models.audit_log import AuditEventType, AuditLog


class AuditLogService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def record(
        self,
        event_type: AuditEventType,
        entity_type: str,
        entity_id: str | None = None,
        actor: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AuditLog:
        audit_log = AuditLog(
            event_type=event_type,
            actor=actor,
            entity_type=entity_type,
            entity_id=entity_id,
            event_metadata=metadata,
        )

        self.db.add(audit_log)

        return audit_log
