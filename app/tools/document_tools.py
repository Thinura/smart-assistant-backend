from typing import Any

from sqlalchemy.orm import Session

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

        if not query:
            return ToolResult(
                success=False,
                error="query is required",
            )

        results = self.document_search_service.search(
            query=query,
            top_k=top_k,
        )

        return ToolResult(
            success=True,
            data={
                "query": query,
                "results": results,
            },
        )
