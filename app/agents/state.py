from typing import TypedDict
from uuid import UUID


class AgentState(TypedDict):
    conversation_id: UUID
    user_message: str
    assistant_message: str | None
    error: str | None
