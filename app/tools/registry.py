from typing import Any

from sqlalchemy.orm import Session

from app.tools.approval_tools import CreateApprovalRequestTool
from app.tools.base import BaseTool, ToolResult
from app.tools.candidate_tools import ReviewCandidateTool
from app.tools.conversation_tools import ConversationSummaryTool
from app.tools.document_tools import SearchDocumentsTool


class ToolRegistry:
    def __init__(self) -> None:
        self._static_tools: dict[str, BaseTool] = {
            ConversationSummaryTool.name: ConversationSummaryTool(),
        }

    def _get_db_tools(self, db: Session | None) -> dict[str, BaseTool]:
        if db is None:
            return {}

        return {
            SearchDocumentsTool.name: SearchDocumentsTool(db),
            ReviewCandidateTool.name: ReviewCandidateTool(db),
            CreateApprovalRequestTool.name: CreateApprovalRequestTool(db),
        }

    def get(self, name: str, db: Session | None = None) -> BaseTool | None:
        if name in self._static_tools:
            return self._static_tools[name]

        return self._get_db_tools(db).get(name)

    def run(
        self,
        name: str,
        payload: dict[str, Any],
        db: Session | None = None,
    ) -> ToolResult:
        tool = self.get(name=name, db=db)

        if tool is None:
            return ToolResult(
                success=False,
                error=f"Tool not found: {name}",
            )

        return tool.run(payload)

    def list_tools(self, db: Session | None = None) -> list[dict[str, str | bool]]:
        tools = {
            **self._static_tools,
            **self._get_db_tools(db),
        }

        return [
            {
                "name": tool.name,
                "description": tool.description,
                "requires_approval": tool.requires_approval,
            }
            for tool in tools.values()
        ]


tool_registry = ToolRegistry()
