from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.candidate_job_match import (
    CandidateJobMatchConfidence,
    CandidateJobMatchRecommendation,
)


class CandidateJobMatchRequest(BaseModel):
    job_description_document_id: UUID
    role_name: str | None = Field(default=None, max_length=255)


class CandidateJobMatchCreate(BaseModel):
    candidate_id: UUID
    cv_document_id: UUID
    job_description_document_id: UUID
    role_name: str | None = None
    summary: str
    match_score: int = Field(ge=0, le=100)
    recommendation: CandidateJobMatchRecommendation
    confidence: CandidateJobMatchConfidence
    matched_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    interview_focus_areas: list[str] = Field(default_factory=list)
    source_metadata: dict = Field(default_factory=dict)


class CandidateJobMatchResponse(BaseModel):
    id: UUID
    candidate_id: UUID
    cv_document_id: UUID
    job_description_document_id: UUID
    role_name: str | None
    summary: str
    match_score: int
    recommendation: CandidateJobMatchRecommendation
    confidence: CandidateJobMatchConfidence
    matched_skills: list[str]
    missing_skills: list[str]
    risks: list[str]
    interview_focus_areas: list[str]
    source_metadata: dict
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
