from typing import TypedDict
from uuid import UUID

from app.agents.intents import AgentIntent


class AgentState(TypedDict):
    conversation_id: UUID
    user_message: str
    intent: AgentIntent
    assistant_message: str | None
    error: str | None
