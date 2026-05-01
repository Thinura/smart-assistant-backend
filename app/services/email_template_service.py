import re

from sqlalchemy.orm import Session

from app.models.audit_log import AuditEventType
from app.models.email_template import EmailTemplate, EmailTemplateType
from app.schemas.email_template import (
    EmailTemplateCreate,
    EmailTemplateRenderResponse,
    EmailTemplateUpdate,
)
from app.services.audit_log_service import AuditLogService

VARIABLE_PATTERN = re.compile(r"{{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*}}")


class EmailTemplateService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_template(self, payload: EmailTemplateCreate) -> EmailTemplate:
        required_variables = self._normalize_variables(payload.required_variables)
        optional_variables = self._normalize_variables(payload.optional_variables)

        template = EmailTemplate(
            name=payload.name,
            template_type=payload.template_type,
            subject_template=payload.subject_template,
            body_template=payload.body_template,
            required_variables=required_variables,
            optional_variables=optional_variables,
            is_active=payload.is_active,
        )

        self.db.add(template)
        self.db.flush()

        AuditLogService(self.db).record(
            event_type=AuditEventType.EMAIL_TEMPLATE_CREATED,
            entity_type="email_template",
            entity_id=str(template.id),
            actor="system",
            metadata={
                "name": template.name,
                "template_type": template.template_type.value,
                "required_variables": required_variables,
                "optional_variables": optional_variables,
            },
        )

        self.db.commit()
        self.db.refresh(template)

        return template

    def update_template(
        self,
        *,
        template: EmailTemplate,
        payload: EmailTemplateUpdate,
    ) -> EmailTemplate:
        update_data = payload.model_dump(exclude_unset=True)

        if "required_variables" in update_data and update_data["required_variables"] is not None:
            update_data["required_variables"] = self._normalize_variables(
                update_data["required_variables"]
            )

        if "optional_variables" in update_data and update_data["optional_variables"] is not None:
            update_data["optional_variables"] = self._normalize_variables(
                update_data["optional_variables"]
            )

        for field, value in update_data.items():
            setattr(template, field, value)

        self.db.flush()

        AuditLogService(self.db).record(
            event_type=AuditEventType.EMAIL_TEMPLATE_UPDATED,
            entity_type="email_template",
            entity_id=str(template.id),
            actor="system",
            metadata={
                "updated_fields": list(update_data.keys()),
            },
        )

        self.db.commit()
        self.db.refresh(template)

        return template

    def render_template(
        self,
        *,
        template: EmailTemplate,
        variables: dict[str, str],
    ) -> EmailTemplateRenderResponse:
        normalized_variables = {key.strip(): str(value) for key, value in variables.items()}

        missing_variables = [
            variable
            for variable in template.required_variables
            if variable not in normalized_variables or not normalized_variables[variable].strip()
        ]

        if missing_variables:
            return EmailTemplateRenderResponse(
                template_id=template.id,
                subject="",
                body="",
                used_variables=normalized_variables,
                missing_variables=missing_variables,
            )

        subject = self._render_text(template.subject_template, normalized_variables)
        body = self._render_text(template.body_template, normalized_variables)

        AuditLogService(self.db).record(
            event_type=AuditEventType.EMAIL_TEMPLATE_RENDERED,
            entity_type="email_template",
            entity_id=str(template.id),
            actor="system",
            metadata={
                "template_type": template.template_type.value,
                "used_variables": sorted(normalized_variables.keys()),
            },
        )

        self.db.commit()

        return EmailTemplateRenderResponse(
            template_id=template.id,
            subject=subject,
            body=body,
            used_variables=normalized_variables,
            missing_variables=[],
        )

    def get_active_template_by_type(
        self,
        template_type: EmailTemplateType,
    ) -> EmailTemplate | None:
        return (
            self.db.query(EmailTemplate)
            .filter(
                EmailTemplate.template_type == template_type,
                EmailTemplate.is_active.is_(True),
            )
            .order_by(EmailTemplate.created_at.desc())
            .first()
        )

    def _render_text(self, template_text: str, variables: dict[str, str]) -> str:
        def replace(match: re.Match[str]) -> str:
            variable_name = match.group(1)
            return variables.get(variable_name, "")

        return VARIABLE_PATTERN.sub(replace, template_text)

    def _normalize_variables(self, variables: list[str]) -> list[str]:
        return sorted({variable.strip() for variable in variables if variable.strip()})

    def extract_variables_from_template(self, subject: str, body: str) -> list[str]:
        variables = set(VARIABLE_PATTERN.findall(subject))
        variables.update(VARIABLE_PATTERN.findall(body))
        return sorted(variables)
