from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from app.api.deps import DbSession
from app.models.tool_call import ToolCall
from app.tools.registry import tool_registry

router = APIRouter()


class ToolRunRequest(BaseModel):
    payload: dict[str, Any]
    agent_run_id: str | None = None


@router.get("")
def list_tools() -> list[dict[str, str | bool]]:
    return tool_registry.list_tools()


@router.post("/{tool_name}/run")
def run_tool(
    tool_name: str,
    request: ToolRunRequest,
    db: DbSession,
) -> dict[str, Any]:
    result = tool_registry.run(tool_name, request.payload)

    tool_call = ToolCall(
        agent_run_id=request.agent_run_id,
        tool_name=tool_name,
        input_payload=request.payload,
        output_payload=result.data,
        success=result.success,
        error_message=result.error,
    )

    db.add(tool_call)
    db.commit()

    response = result.model_dump()
    response["tool_call_id"] = str(tool_call.id)

    return response