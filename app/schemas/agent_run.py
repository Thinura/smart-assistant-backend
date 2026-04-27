from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.agent_run import AgentRunStatus
from app.models.approval_request import ApprovalActionType, ApprovalStatus
from app.models.audit_log import AuditEventType


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


class AgentRunToolCallResponse(BaseModel):
    id: UUID
    agent_run_id: UUID | None
    tool_name: str
    input_payload: dict[str, Any]
    output_payload: dict[str, Any] | None
    success: bool
    error_message: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AgentRunApprovalResponse(BaseModel):
    id: UUID
    agent_run_id: UUID | None
    action_type: ApprovalActionType
    status: ApprovalStatus
    title: str
    description: str | None
    action_payload: dict[str, Any]
    execution_result: dict[str, Any] | None
    reviewed_by: str | None
    review_comment: str | None
    created_at: datetime
    reviewed_at: datetime | None
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AgentRunAuditLogResponse(BaseModel):
    id: UUID
    event_type: AuditEventType
    actor: str | None
    entity_type: str
    entity_id: str | None
    event_metadata: dict[str, Any] | None = Field(alias="event_metadata")
    created_at: datetime

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class AgentRunTraceSummary(BaseModel):
    agent_run_id: UUID
    status: AgentRunStatus
    intent: str | None
    tool_call_count: int
    approval_request_count: int
    audit_log_count: int
    has_error: bool


class AgentRunTraceResponse(BaseModel):
    summary: AgentRunTraceSummary
    agent_run: AgentRunResponse
    tool_calls: list[AgentRunToolCallResponse]
    approval_requests: list[AgentRunApprovalResponse]
    audit_logs: list[AgentRunAuditLogResponse]
