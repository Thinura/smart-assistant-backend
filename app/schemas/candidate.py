from datetime import datetime
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
