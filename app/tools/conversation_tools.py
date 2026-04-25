from typing import Any

from app.tools.base import BaseTool, ToolResult


class ConversationSummaryTool(BaseTool):
    name = "conversation_summary"
    description = "Returns a simple summary of what the conversation tool can do."

    def run(self, payload: dict[str, Any]) -> ToolResult:
        conversation_id = payload.get("conversation_id")

        if conversation_id is None:
            return ToolResult(
                success=False,
                error="conversation_id is required",
            )

        return ToolResult(
            success=True,
            data={
                "conversation_id": str(conversation_id),
                "summary": "Conversation tools are available.",
            },
        )
