from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import DbSession
from app.models.email_template import EmailTemplate, EmailTemplateType
from app.schemas.email_template import (
    EmailTemplateCreate,
    EmailTemplateRenderRequest,
    EmailTemplateRenderResponse,
    EmailTemplateResponse,
    EmailTemplateUpdate,
)
from app.services.email_template_service import EmailTemplateService

router = APIRouter()

TEMPLATE_TYPE_QUERY = Query(default=None, alias="template_type")
ACTIVE_QUERY = Query(default=None, alias="is_active")
LIMIT_QUERY = Query(default=100, ge=1, le=500)


@router.post("", response_model=EmailTemplateResponse, status_code=status.HTTP_201_CREATED)
def create_email_template(
    payload: EmailTemplateCreate,
    db: DbSession,
) -> EmailTemplate:
    return EmailTemplateService(db).create_template(payload)


@router.get("", response_model=list[EmailTemplateResponse])
def list_email_templates(
    db: DbSession,
    template_type_filter: EmailTemplateType | None = TEMPLATE_TYPE_QUERY,
    is_active: bool | None = ACTIVE_QUERY,
    limit: int = LIMIT_QUERY,
) -> list[EmailTemplate]:
    query = db.query(EmailTemplate)

    if template_type_filter is not None:
        query = query.filter(EmailTemplate.template_type == template_type_filter)

    if is_active is not None:
        query = query.filter(EmailTemplate.is_active == is_active)

    return query.order_by(EmailTemplate.created_at.desc()).limit(limit).all()


@router.get("/{template_id}", response_model=EmailTemplateResponse)
def get_email_template(
    template_id: UUID,
    db: DbSession,
) -> EmailTemplate:
    template = db.get(EmailTemplate, template_id)

    if template is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email template not found",
        )

    return template


@router.patch("/{template_id}", response_model=EmailTemplateResponse)
def update_email_template(
    template_id: UUID,
    payload: EmailTemplateUpdate,
    db: DbSession,
) -> EmailTemplate:
    template = db.get(EmailTemplate, template_id)

    if template is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email template not found",
        )

    return EmailTemplateService(db).update_template(
        template=template,
        payload=payload,
    )


@router.post("/{template_id}/render", response_model=EmailTemplateRenderResponse)
def render_email_template(
    template_id: UUID,
    payload: EmailTemplateRenderRequest,
    db: DbSession,
) -> EmailTemplateRenderResponse:
    template = db.get(EmailTemplate, template_id)

    if template is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email template not found",
        )

    if not template.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email template is inactive",
        )

    rendered = EmailTemplateService(db).render_template(
        template=template,
        variables=payload.variables,
    )

    if rendered.missing_variables:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=(
                "Missing required template variables: " + ", ".join(rendered.missing_variables)
            ),
        )

    return rendered
