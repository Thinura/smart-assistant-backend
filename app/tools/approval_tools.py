from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.approval_request import ApprovalActionType, ApprovalRequest
from app.tools.base import BaseTool, ToolResult


class CreateApprovalRequestTool(BaseTool):
    name = "create_approval_request"
    description = "Creates a human approval request for sensitive agent actions."
    requires_approval = False

    def __init__(self, db: Session) -> None:
        self.db = db

    def run(self, payload: dict[str, Any]) -> ToolResult:
        action_type = self._parse_action_type(payload.get("action_type"))
        title = str(payload.get("title", "")).strip()
        description = payload.get("description")
        action_payload = payload.get("action_payload")
        agent_run_id = self._parse_uuid(payload.get("agent_run_id"))

        if action_type is None:
            return ToolResult(
                success=False,
                error="action_type is required and must be valid",
            )

        if not title:
            return ToolResult(
                success=False,
                error="title is required",
            )

        if not isinstance(action_payload, dict):
            return ToolResult(
                success=False,
                error="action_payload must be an object",
            )

        approval_request = ApprovalRequest(
            agent_run_id=agent_run_id,
            action_type=action_type,
            title=title,
            description=str(description) if description else None,
            action_payload=action_payload,
        )

        self.db.add(approval_request)
        self.db.commit()
        self.db.refresh(approval_request)

        return ToolResult(
            success=True,
            data={
                "approval_request_id": str(approval_request.id),
                "status": approval_request.status.value,
                "action_type": approval_request.action_type.value,
                "title": approval_request.title,
            },
        )

    def _parse_action_type(self, value: Any) -> ApprovalActionType | None:
        if value is None:
            return None

        try:
            return ApprovalActionType(str(value).lower())
        except ValueError:
            return None

    def _parse_uuid(self, value: Any) -> UUID | None:
        if value is None:
            return None

        try:
            return UUID(str(value))
        except ValueError:
            return None
