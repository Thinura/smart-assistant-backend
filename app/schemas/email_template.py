from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.email_template import EmailTemplateType


class EmailTemplateCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    template_type: EmailTemplateType
    subject_template: str = Field(min_length=1, max_length=500)
    body_template: str = Field(min_length=1)
    required_variables: list[str] = Field(default_factory=list)
    optional_variables: list[str] = Field(default_factory=list)
    is_active: bool = True


class EmailTemplateUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    template_type: EmailTemplateType | None = None
    subject_template: str | None = Field(default=None, min_length=1, max_length=500)
    body_template: str | None = Field(default=None, min_length=1)
    required_variables: list[str] | None = None
    optional_variables: list[str] | None = None
    is_active: bool | None = None


class EmailTemplateResponse(BaseModel):
    id: UUID
    name: str
    template_type: EmailTemplateType
    subject_template: str
    body_template: str
    required_variables: list[str]
    optional_variables: list[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EmailTemplateRenderRequest(BaseModel):
    variables: dict[str, str]


class EmailTemplateRenderResponse(BaseModel):
    template_id: UUID
    subject: str
    body: str
    used_variables: dict[str, str]
    missing_variables: list[str]
