from fastapi import APIRouter, Query

from app.api.deps import DbSession
from app.models.audit_log import AuditEventType, AuditLog
from app.schemas.audit_log import AuditLogResponse

router = APIRouter()


@router.get("", response_model=list[AuditLogResponse])
def list_audit_logs(
    db: DbSession,
    event_type: AuditEventType | None = None,
    entity_type: str | None = None,
    entity_id: str | None = None,
    actor: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
) -> list[AuditLog]:
    query = db.query(AuditLog)

    if event_type is not None:
        query = query.filter(AuditLog.event_type == event_type)

    if entity_type is not None:
        query = query.filter(AuditLog.entity_type == entity_type)

    if entity_id is not None:
        query = query.filter(AuditLog.entity_id == entity_id)

    if actor is not None:
        query = query.filter(AuditLog.actor == actor)

    return query.order_by(AuditLog.created_at.desc()).limit(limit).all()
