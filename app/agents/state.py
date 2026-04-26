from typing import Any, TypedDict
from uuid import UUID

from app.agents.intents import AgentIntent


class AgentState(TypedDict):
    conversation_id: UUID
    agent_run_id: UUID | None
    user_message: str
    intent: AgentIntent
    assistant_message: str | None
    tool_results: list[dict[str, Any]]
    error: str | None