from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.document import DocumentType
from app.services.document_search_service import DocumentSearchService
from app.tools.base import BaseTool, ToolResult


class SearchDocumentsTool(BaseTool):
    name = "search_documents"
    description = "Searches uploaded document chunks using vector similarity."
    requires_approval = False

    def __init__(self, db: Session) -> None:
        self.document_search_service = DocumentSearchService(db)

    def run(self, payload: dict[str, Any]) -> ToolResult:
        query = str(payload.get("query", "")).strip()
        top_k = int(payload.get("top_k", 5))

        document_type = self._parse_document_type(payload.get("document_type"))
        document_id = self._parse_document_id(payload.get("document_id"))

        if not query:
            return ToolResult(
                success=False,
                error="query is required",
            )

        results = self.document_search_service.search(
            query=query,
            top_k=top_k,
            document_type=document_type,
            document_id=document_id,
        )

        return ToolResult(
            success=True,
            data={
                "query": query,
                "document_type": document_type.value if document_type else None,
                "document_id": str(document_id) if document_id else None,
                "results": results,
            },
        )

    def _parse_document_type(self, value: Any) -> DocumentType | None:
        if value is None:
            return None

        try:
            return DocumentType(str(value).lower())
        except ValueError:
            return None

    def _parse_document_id(self, value: Any) -> UUID | None:
        if value is None:
            return None

        try:
            return UUID(str(value))
        except ValueError:
            return None
