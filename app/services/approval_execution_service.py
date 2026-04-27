from typing import Any

from app.models.approval_request import (
    ApprovalActionType,
    ApprovalRequest,
    ApprovalStatus,
)


class ApprovalExecutionService:
    def execute(self, approval_request: ApprovalRequest) -> dict[str, Any]:
        if approval_request.status != ApprovalStatus.APPROVED:
            raise ValueError("Only approved approval requests can be executed")

        if approval_request.action_type == ApprovalActionType.EMAIL_DRAFT:
            return self._execute_email_draft(approval_request)

        if approval_request.action_type == ApprovalActionType.CANDIDATE_STATUS_CHANGE:
            return self._execute_candidate_status_change(approval_request)

        if approval_request.action_type == ApprovalActionType.GENERAL_AGENT_ACTION:
            return self._execute_general_agent_action(approval_request)

        if approval_request.action_type == ApprovalActionType.SEND_EMAIL:
            return self._execute_send_email(approval_request)

        raise ValueError(f"Unsupported approval action type: {approval_request.action_type}")

    def _execute_email_draft(
        self,
        approval_request: ApprovalRequest,
    ) -> dict[str, Any]:
        payload = approval_request.action_payload

        return {
            "executed": True,
            "mode": "dry_run",
            "action_type": approval_request.action_type.value,
            "message": "Email draft execution recorded. Email sending is not enabled yet.",
            "candidate_id": payload.get("candidate_id"),
            "candidate_email": payload.get("candidate_email"),
            "subject": payload.get("subject"),
        }

    def _execute_send_email(
        self,
        approval_request: ApprovalRequest,
    ) -> dict[str, Any]:
        payload = approval_request.action_payload

        return {
            "executed": True,
            "mode": "dry_run",
            "action_type": approval_request.action_type.value,
            "message": "Send email action recorded. Real email sending is not enabled yet.",
            "to": payload.get("to") or payload.get("candidate_email"),
            "subject": payload.get("subject"),
        }

    def _execute_candidate_status_change(
        self,
        approval_request: ApprovalRequest,
    ) -> dict[str, Any]:
        payload = approval_request.action_payload

        return {
            "executed": True,
            "mode": "dry_run",
            "action_type": approval_request.action_type.value,
            "message": "Candidate status change execution recorded. "
            "Status update is not enabled yet.",
            "candidate_id": payload.get("candidate_id"),
            "target_status": payload.get("target_status"),
        }

    def _execute_general_agent_action(
        self,
        approval_request: ApprovalRequest,
    ) -> dict[str, Any]:
        return {
            "executed": True,
            "mode": "dry_run",
            "action_type": approval_request.action_type.value,
            "message": "General agent action execution recorded.",
        }
