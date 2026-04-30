from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.candidate_review import (
    CandidateReviewConfidence,
    CandidateReviewRecommendation,
)


class CandidateReviewResponse(BaseModel):
    id: UUID
    candidate_id: UUID
    agent_run_id: UUID | None
    cv_document_id: UUID | None
    role_applied_for: str | None
    summary: str
    score: int | None
    recommendation: CandidateReviewRecommendation
    confidence: CandidateReviewConfidence
    strengths: list[str]
    risks: list[str]
    interview_focus_areas: list[str]
    source_metadata: dict
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CandidateReviewCreate(BaseModel):
    candidate_id: UUID
    agent_run_id: UUID | None = None
    cv_document_id: UUID | None = None
    role_applied_for: str | None = Field(default=None, max_length=255)
    summary: str
    score: int | None = Field(default=None, ge=0, le=100)
    recommendation: CandidateReviewRecommendation
    confidence: CandidateReviewConfidence
    strengths: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    interview_focus_areas: list[str] = Field(default_factory=list)
    source_metadata: dict = Field(default_factory=dict)
