from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.candidate import CandidateStatus


class CandidateCreate(BaseModel):
    full_name: str = Field(min_length=1, max_length=255)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=50)
    role_applied_for: str | None = Field(default=None, max_length=255)
    cv_document_id: UUID | None = None
    notes: str | None = None


class CandidateUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=50)
    role_applied_for: str | None = Field(default=None, max_length=255)
    status: CandidateStatus | None = None
    cv_document_id: UUID | None = None
    notes: str | None = None

class CandidateStatusUpdate(BaseModel):
    status: CandidateStatus
    reason: str | None = Field(default=None, max_length=1000)
    updated_by: str = Field(default="system", max_length=255)

class CandidateResponse(BaseModel):
    id: UUID
    full_name: str
    email: EmailStr | None
    phone: str | None
    role_applied_for: str | None
    status: CandidateStatus
    cv_document_id: UUID | None
    notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CandidateTimelineDocumentResponse(BaseModel):
    id: UUID
    original_filename: str
    document_type: str
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CandidateTimelineAuditLogResponse(BaseModel):
    id: UUID
    event_type: str
    actor: str | None
    entity_type: str
    entity_id: str | None
    event_metadata: dict[str, Any] | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CandidateTimelineAgentRunResponse(BaseModel):
    id: UUID
    status: str
    input_message: str
    output_message: str | None
    error_message: str | None
    run_metadata: dict[str, Any] | None
    started_at: datetime
    completed_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class CandidateTimelineApprovalResponse(BaseModel):
    id: UUID
    agent_run_id: UUID | None
    action_type: str
    status: str
    title: str
    description: str | None
    action_payload: dict[str, Any]
    reviewed_by: str | None
    review_comment: str | None
    created_at: datetime
    reviewed_at: datetime | None
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CandidateTimelineSummary(BaseModel):
    candidate_id: UUID
    has_cv: bool
    audit_log_count: int
    agent_run_count: int
    approval_request_count: int
    pending_approval_count: int


class CandidateTimelineResponse(BaseModel):
    summary: CandidateTimelineSummary
    candidate: CandidateResponse
    cv_document: CandidateTimelineDocumentResponse | None
    audit_logs: list[CandidateTimelineAuditLogResponse]
    agent_runs: list[CandidateTimelineAgentRunResponse]
    approval_requests: list[CandidateTimelineApprovalResponse]
