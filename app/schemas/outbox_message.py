from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.outbox_message import OutboxMessageStatus


class OutboxMessageResponse(BaseModel):
    id: UUID
    approval_request_id: UUID | None
    candidate_id: UUID | None
    recipient_email: EmailStr | None
    subject: str | None
    body: str
    status: OutboxMessageStatus
    provider_message_id: str | None
    error_message: str | None
    created_at: datetime
    sent_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class OutboxMarkSentRequest(BaseModel):
    provider_message_id: str | None = Field(default=None, max_length=255)


class OutboxBulkSendRequest(BaseModel):
    limit: int = Field(default=50, ge=1, le=500)
    include_failed: bool = False


class OutboxBulkSendItemResponse(BaseModel):
    id: str
    status: str
    provider_message_id: str | None = None
    error_message: str | None = None


class OutboxBulkSendResponse(BaseModel):
    total: int
    sent_count: int
    failed_count: int
    results: list[OutboxBulkSendItemResponse]
