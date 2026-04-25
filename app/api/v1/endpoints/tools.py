from fastapi import APIRouter

from app.tools.registry import tool_registry

router = APIRouter()


@router.get("")
def list_tools() -> list[dict[str, str]]:
    return tool_registry.list_tools()


@router.post("/{tool_name}/run")
def run_tool(
    tool_name: str,
    payload: dict,
) -> dict:
    result = tool_registry.run(tool_name, payload)
    return result.model_dump()
