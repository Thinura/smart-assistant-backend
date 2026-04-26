from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.document import DocumentStatus, DocumentType


class DocumentListResponse(BaseModel):
    id: UUID
    original_filename: str
    content_type: str
    file_size: int
    document_type: DocumentType
    status: DocumentStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentDetailResponse(BaseModel):
    id: UUID
    original_filename: str
    storage_path: str
    content_type: str
    file_size: int
    extracted_text: str | None
    document_type: DocumentType
    status: DocumentStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
