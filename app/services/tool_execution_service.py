from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.tool_call import ToolCall
from app.tools.base import ToolResult
from app.tools.registry import tool_registry


class ToolExecutionService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def run_tool(
        self,
        tool_name: str,
        payload: dict[str, Any],
        agent_run_id: UUID | None = None,
    ) -> tuple[ToolResult, ToolCall]:
        result = tool_registry.run(tool_name, payload)

        tool_call = ToolCall(
            agent_run_id=agent_run_id,
            tool_name=tool_name,
            input_payload=payload,
            output_payload=result.data,
            success=result.success,
            error_message=result.error,
        )

        self.db.add(tool_call)
        self.db.commit()
        self.db.refresh(tool_call)

        return result, tool_call
