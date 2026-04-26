from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.services.embedding_service import EmbeddingService
from app.tools.base import BaseTool, ToolResult


class SearchDocumentsTool(BaseTool):
    name = "search_documents"
    description = "Searches uploaded document chunks using vector similarity."
    requires_approval = False

    def __init__(self, db: Session) -> None:
        self.db = db
        self.embedding_service = EmbeddingService()

    def run(self, payload: dict[str, Any]) -> ToolResult:
        query = str(payload.get("query", "")).strip()
        top_k = int(payload.get("top_k", 5))

        if not query:
            return ToolResult(
                success=False,
                error="query is required",
            )

        query_embedding = self.embedding_service.generate_embedding(query)

        similarity_score = DocumentChunk.embedding.cosine_distance(query_embedding).label(
            "distance"
        )

        statement = (
            select(
                DocumentChunk.id,
                DocumentChunk.document_id,
                DocumentChunk.chunk_index,
                DocumentChunk.content,
                Document.original_filename,
                similarity_score,
            )
            .join(Document, Document.id == DocumentChunk.document_id)
            .where(DocumentChunk.embedding.is_not(None))
            .order_by(similarity_score)
            .limit(top_k)
        )

        rows = self.db.execute(statement).all()

        results = [
            {
                "chunk_id": str(row.id),
                "document_id": str(row.document_id),
                "chunk_index": row.chunk_index,
                "content": row.content,
                "source": row.original_filename,
                "distance": float(row.distance),
            }
            for row in rows
        ]

        return ToolResult(
            success=True,
            data={
                "query": query,
                "results": results,
            },
        )
