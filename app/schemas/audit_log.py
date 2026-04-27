from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.audit_log import AuditEventType


class AuditLogResponse(BaseModel):
    id: UUID
    event_type: AuditEventType
    actor: str | None
    entity_type: str
    entity_id: str | None
    metadata: dict | None = Field(None, alias="event_metadata")
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
