from typing import Any
from uuid import UUID

from fastapi import APIRouter
from pydantic import BaseModel

from app.api.deps import DbSession
from app.services.tool_execution_service import ToolExecutionService
from app.tools.registry import tool_registry

router = APIRouter()


class ToolRunRequest(BaseModel):
    payload: dict[str, Any]
    agent_run_id: UUID | None = None


@router.get("")
def list_tools() -> list[dict[str, str | bool]]:
    return tool_registry.list_tools()


@router.post("/{tool_name}/run")
def run_tool(
    tool_name: str,
    request: ToolRunRequest,
    db: DbSession,
) -> dict[str, Any]:
    tool_execution_service = ToolExecutionService(db)

    result, tool_call = tool_execution_service.run_tool(
        tool_name=tool_name,
        payload=request.payload,
        agent_run_id=request.agent_run_id,
    )

    response = result.model_dump()
    response["tool_call_id"] = str(tool_call.id)

    return response