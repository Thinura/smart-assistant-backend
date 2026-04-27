from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.document import Document, DocumentType
from app.models.document_chunk import DocumentChunk
from app.services.embedding_service import EmbeddingService


class DocumentSearchService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.embedding_service = EmbeddingService()

    def search(
        self,
        query: str,
        top_k: int = 5,
        document_type: DocumentType | None = None,
        document_id: UUID | None = None,
    ) -> list[dict[str, Any]]:
        cleaned_query = query.strip()

        if not cleaned_query:
            return []

        query_embedding = self.embedding_service.generate_embedding(cleaned_query)

        distance = DocumentChunk.embedding.cosine_distance(query_embedding).label("distance")

        statement = (
            select(
                DocumentChunk.id,
                DocumentChunk.document_id,
                DocumentChunk.chunk_index,
                DocumentChunk.content,
                Document.original_filename,
                Document.document_type,
                distance,
            )
            .join(Document, Document.id == DocumentChunk.document_id)
            .where(DocumentChunk.embedding.is_not(None))
        )

        if document_type is not None:
            statement = statement.where(Document.document_type == document_type)

        if document_id is not None:
            statement = statement.where(Document.id == document_id)

        statement = statement.order_by(distance).limit(top_k)

        rows = self.db.execute(statement).all()

        return [
            {
                "chunk_id": str(row.id),
                "document_id": str(row.document_id),
                "chunk_index": row.chunk_index,
                "content": row.content,
                "source": row.original_filename,
                "document_type": row.document_type.value,
                "distance": float(row.distance),
            }
            for row in rows
        ]
