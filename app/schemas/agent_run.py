from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.agent_run import AgentRunStatus


class AgentRunResponse(BaseModel):
    id: UUID
    conversation_id: UUID
    status: AgentRunStatus
    input_message: str
    output_message: str | None
    error_message: str | None
    run_metadata: dict | None
    started_at: datetime
    completed_at: datetime | None

    model_config = ConfigDict(from_attributes=True)
