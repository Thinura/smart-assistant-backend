from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.candidate_workflow import CandidateWorkflowStatus, CandidateWorkflowType


class CandidateWorkflowCreate(BaseModel):
    candidate_id: UUID
    agent_run_id: UUID | None = None
    workflow_type: CandidateWorkflowType
    status: CandidateWorkflowStatus
    role_name: str | None = None
    candidate_review_id: UUID | None = None
    candidate_job_match_id: UUID | None = None
    interview_kit_id: UUID | None = None
    approval_request_id: UUID | None = None
    score: int | None = None
    recommendation: str | None = None
    summary: str | None = None
    workflow_metadata: dict = {}


class CandidateWorkflowResponse(BaseModel):
    id: UUID
    candidate_id: UUID
    agent_run_id: UUID | None
    workflow_type: CandidateWorkflowType
    status: CandidateWorkflowStatus
    role_name: str | None
    candidate_review_id: UUID | None
    candidate_job_match_id: UUID | None
    interview_kit_id: UUID | None
    approval_request_id: UUID | None
    score: int | None
    recommendation: str | None
    summary: str | None
    workflow_metadata: dict
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
