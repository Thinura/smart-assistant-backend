from sqlalchemy.orm import Session

from app.models.approval_request import ApprovalRequest, ApprovalStatus
from app.models.audit_log import AuditEventType
from app.models.email_template import EmailTemplate
from app.schemas.approval_request import ApprovalRequestUpdate
from app.services.audit_log_service import AuditLogService
from app.services.email_template_service import EmailTemplateService


class ApprovalRequestService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def update_request(
        self,
        *,
        approval_request: ApprovalRequest,
        payload: ApprovalRequestUpdate,
    ) -> ApprovalRequest:
        if approval_request.status != ApprovalStatus.PENDING:
            raise ValueError("Only pending approval requests can be updated")

        update_data = payload.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(approval_request, field, value)

        self.db.flush()

        AuditLogService(self.db).record(
            event_type=AuditEventType.APPROVAL_REQUEST_UPDATED,
            entity_type="approval_request",
            entity_id=str(approval_request.id),
            actor="system",
            metadata={
                "updated_fields": list(update_data.keys()),
                "status": approval_request.status.value,
            },
        )

        self.db.commit()
        self.db.refresh(approval_request)

        return approval_request

    def render_template_for_request(
        self,
        *,
        approval_request: ApprovalRequest,
        variables: dict[str, str],
    ) -> ApprovalRequest:
        if approval_request.status != ApprovalStatus.PENDING:
            raise ValueError("Only pending approval requests can be rendered")

        action_payload = dict(approval_request.action_payload or {})

        template_id = action_payload.get("template_id")

        if not template_id:
            raise ValueError("Approval request does not have a template_id")

        template = self.db.get(EmailTemplate, template_id)

        if template is None:
            raise ValueError("Email template not found")

        existing_variables = action_payload.get("template_variables") or {}

        merged_variables = {
            **existing_variables,
            **variables,
        }

        template_service = EmailTemplateService(self.db)

        rendered = template_service.render_template(
            template=template,
            variables=merged_variables,
        )

        if rendered.missing_variables:
            action_payload["template_variables"] = rendered.used_variables
            action_payload["missing_template_variables"] = rendered.missing_variables

            approval_request.action_payload = action_payload

            self.db.flush()

            AuditLogService(self.db).record(
                event_type=AuditEventType.APPROVAL_REQUEST_UPDATED,
                entity_type="approval_request",
                entity_id=str(approval_request.id),
                actor="system",
                metadata={
                    "updated_fields": ["action_payload"],
                    "missing_template_variables": rendered.missing_variables,
                },
            )

            self.db.commit()
            self.db.refresh(approval_request)

            raise ValueError(
                "Missing required template variables: " + ", ".join(rendered.missing_variables)
            )

        action_payload["subject"] = rendered.subject
        action_payload["draft_body"] = rendered.body
        action_payload["template_variables"] = rendered.used_variables
        action_payload.pop("missing_template_variables", None)

        approval_request.action_payload = action_payload

        self.db.flush()

        AuditLogService(self.db).record(
            event_type=AuditEventType.APPROVAL_REQUEST_UPDATED,
            entity_type="approval_request",
            entity_id=str(approval_request.id),
            actor="system",
            metadata={
                "updated_fields": ["action_payload"],
                "template_id": str(template.id),
                "rendered": True,
            },
        )

        self.db.commit()
        self.db.refresh(approval_request)

        return approval_request
