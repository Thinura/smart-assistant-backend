from uuid import UUID

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    conversation_id: UUID
    message: str = Field(min_length=1)


class ChatResponse(BaseModel):
    conversation_id: UUID
    agent_run_id: UUID
    user_message: str
    assistant_message: str
