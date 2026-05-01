from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.interview_kit import InterviewKitStatus


class InterviewKitGenerateRequest(BaseModel):
    job_description_document_id: UUID | None = None
    role_name: str | None = Field(default=None, max_length=255)


class InterviewQuestion(BaseModel):
    question: str
    purpose: str | None = None
    expected_signals: list[str] = Field(default_factory=list)


class EvaluationRubricItem(BaseModel):
    area: str
    strong_signal: str
    weak_signal: str


class InterviewKitCreate(BaseModel):
    candidate_id: UUID
    cv_document_id: UUID | None = None
    job_description_document_id: UUID | None = None
    candidate_review_id: UUID | None = None
    candidate_job_match_id: UUID | None = None
    role_name: str | None = None
    status: InterviewKitStatus = InterviewKitStatus.GENERATED
    summary: str
    technical_questions: list[dict] = Field(default_factory=list)
    behavioral_questions: list[dict] = Field(default_factory=list)
    risk_based_questions: list[dict] = Field(default_factory=list)
    evaluation_rubric: list[dict] = Field(default_factory=list)
    source_metadata: dict = Field(default_factory=dict)


class InterviewKitResponse(BaseModel):
    id: UUID
    candidate_id: UUID
    cv_document_id: UUID | None
    job_description_document_id: UUID | None
    candidate_review_id: UUID | None
    candidate_job_match_id: UUID | None
    role_name: str | None
    status: InterviewKitStatus
    summary: str
    technical_questions: list[dict]
    behavioral_questions: list[dict]
    risk_based_questions: list[dict]
    evaluation_rubric: list[dict]
    source_metadata: dict
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
