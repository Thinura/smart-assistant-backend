from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.agent_run import AgentRunStatus
from app.models.approval_request import ApprovalActionType, ApprovalStatus
from app.models.message import MessageRole


class ConversationCreate(BaseModel):
    title: str | None = Field(default=None, max_length=255)


class ConversationResponse(BaseModel):
    id: UUID
    title: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ConversationTraceMessageResponse(BaseModel):
    id: UUID
    conversation_id: UUID
    role: MessageRole
    content: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ConversationTraceAgentRunResponse(BaseModel):
    id: UUID
    conversation_id: UUID
    status: AgentRunStatus
    input_message: str
    output_message: str | None
    error_message: str | None
    run_metadata: dict[str, Any] | None
    started_at: datetime
    completed_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class ConversationTraceToolCallResponse(BaseModel):
    id: UUID
    agent_run_id: UUID | None
    tool_name: str
    success: bool
    error_message: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ConversationTraceApprovalResponse(BaseModel):
    id: UUID
    agent_run_id: UUID | None
    action_type: ApprovalActionType
    status: ApprovalStatus
    title: str
    description: str | None
    created_at: datetime
    reviewed_at: datetime | None
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ConversationTraceSummary(BaseModel):
    conversation_id: UUID
    message_count: int
    agent_run_count: int
    tool_call_count: int
    approval_request_count: int
    pending_approval_count: int
    has_failed_run: bool


class ConversationTraceResponse(BaseModel):
    summary: ConversationTraceSummary
    conversation: ConversationResponse
    messages: list[ConversationTraceMessageResponse]
    agent_runs: list[ConversationTraceAgentRunResponse]
    tool_calls: list[ConversationTraceToolCallResponse]
    approval_requests: list[ConversationTraceApprovalResponse]
