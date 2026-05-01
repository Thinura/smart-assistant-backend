from sqlalchemy.orm import Session

from app.models.approval_request import ApprovalRequest, ApprovalStatus
from app.models.audit_log import AuditEventType
from app.schemas.approval_request import ApprovalRequestUpdate
from app.services.audit_log_service import AuditLogService


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
