from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.approval_request import ApprovalActionType, ApprovalStatus


class ApprovalTemplateRenderRequest(BaseModel):
    variables: dict[str, str]


class ApprovalRequestCreate(BaseModel):
    agent_run_id: UUID | None = None
    action_type: ApprovalActionType
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    action_payload: dict[str, Any]


class ApprovalReviewRequest(BaseModel):
    reviewed_by: str = Field(min_length=1, max_length=255)
    review_comment: str | None = None


class ApprovalRequestResponse(BaseModel):
    id: UUID
    agent_run_id: UUID | None
    action_type: ApprovalActionType
    status: ApprovalStatus
    title: str
    description: str | None
    action_payload: dict[str, Any]
    execution_result: dict[str, Any] | None = None
    reviewed_by: str | None
    review_comment: str | None
    created_at: datetime
    reviewed_at: datetime | None
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ApprovalRequestUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    action_payload: dict[str, Any] | None = None
