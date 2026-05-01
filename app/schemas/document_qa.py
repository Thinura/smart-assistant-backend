from pydantic import BaseModel, Field

from app.models.document import DocumentType
from app.schemas.document_search import DocumentSearchResult


class DocumentAskRequest(BaseModel):
    question: str = Field(min_length=1)
    document_type: DocumentType | None = None
    limit: int = Field(default=5, ge=1, le=10)


class DocumentAskResponse(BaseModel):
    question: str
    answer: str
    source_count: int
    sources: list[DocumentSearchResult]
