from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class DocumentChunkResponse(BaseModel):
    id: UUID
    document_id: UUID
    chunk_index: int
    content: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
