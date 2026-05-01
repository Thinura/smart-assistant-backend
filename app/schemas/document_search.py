from uuid import UUID

from pydantic import BaseModel, Field

from app.models.document import DocumentType


class DocumentSearchRequest(BaseModel):
    query: str = Field(min_length=1)
    document_type: DocumentType | None = None
    limit: int = Field(default=5, ge=1, le=20)


class DocumentSearchResult(BaseModel):
    document_id: UUID
    chunk_id: UUID
    original_filename: str
    document_type: DocumentType
    chunk_index: int
    content: str
    similarity_score: float


class DocumentSearchResponse(BaseModel):
    query: str
    result_count: int
    results: list[DocumentSearchResult]
