from sqlalchemy.orm import Session

from app.models.document import Document, DocumentType
from app.models.document_chunk import DocumentChunk
from app.schemas.document_search import DocumentSearchResult
from app.services.embedding_service import EmbeddingService


class DocumentSearchService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.embedding_service = EmbeddingService()

    def search(
        self,
        *,
        query: str,
        document_type: DocumentType | None = None,
        limit: int = 5,
    ) -> list[DocumentSearchResult]:
        query_embedding = self.embedding_service.generate_embedding(query)

        distance = DocumentChunk.embedding.cosine_distance(query_embedding)

        db_query = self.db.query(
            Document.id.label("document_id"),
            DocumentChunk.id.label("chunk_id"),
            Document.original_filename.label("original_filename"),
            Document.document_type.label("document_type"),
            DocumentChunk.chunk_index.label("chunk_index"),
            DocumentChunk.content.label("content"),
            distance.label("distance"),
        ).join(Document, Document.id == DocumentChunk.document_id)

        if document_type is not None:
            db_query = db_query.filter(Document.document_type == document_type)

        rows = db_query.order_by(distance.asc()).limit(limit).all()

        return [
            DocumentSearchResult(
                document_id=row.document_id,
                chunk_id=row.chunk_id,
                original_filename=row.original_filename,
                document_type=row.document_type,
                chunk_index=row.chunk_index,
                content=row.content,
                similarity_score=round(1 - float(row.distance), 4),
            )
            for row in rows
        ]
