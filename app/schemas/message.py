from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.message import MessageRole


class MessageResponse(BaseModel):
    id: UUID
    conversation_id: UUID
    role: MessageRole
    content: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)