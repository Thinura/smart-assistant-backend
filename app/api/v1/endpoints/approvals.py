from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.api.deps import DbSession
from app.models.approval_request import ApprovalRequest, ApprovalStatus
from app.models.audit_log import AuditEventType
from app.schemas.approval_request import (
    ApprovalRequestCreate,
    ApprovalRequestResponse,
    ApprovalReviewRequest,
)
from app.services.approval_execution_service import ApprovalExecutionService
from app.services.audit_log_service import AuditLogService

router = APIRouter()


@router.post(
    "",
    response_model=ApprovalRequestResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_approval_request(
    payload: ApprovalRequestCreate,
    db: DbSession,
) -> ApprovalRequest:
    approval_request = ApprovalRequest(**payload.model_dump())

    db.add(approval_request)
    db.flush()

    AuditLogService(db).record(
        event_type=AuditEventType.APPROVAL_CREATED,
        entity_type="approval_request",
        entity_id=str(approval_request.id),
        actor="system",
        metadata={
            "action_type": approval_request.action_type.value,
            "title": approval_request.title,
            "agent_run_id": str(approval_request.agent_run_id)
            if approval_request.agent_run_id
            else None,
        },
    )
    db.commit()
    db.refresh(approval_request)

    return approval_request


@router.get("", response_model=list[ApprovalRequestResponse])
def list_approval_requests(
    db: DbSession,
) -> list[ApprovalRequest]:
    return db.query(ApprovalRequest).order_by(ApprovalRequest.created_at.desc()).all()


@router.get("/{approval_request_id}", response_model=ApprovalRequestResponse)
def get_approval_request(
    approval_request_id: UUID,
    db: DbSession,
) -> ApprovalRequest:
    approval_request = db.get(ApprovalRequest, approval_request_id)

    if approval_request is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Approval request not found",
        )

    return approval_request


@router.post("/{approval_request_id}/approve", response_model=ApprovalRequestResponse)
def approve_request(
    approval_request_id: UUID,
    payload: ApprovalReviewRequest,
    db: DbSession,
) -> ApprovalRequest:
    approval_request = db.get(ApprovalRequest, approval_request_id)

    if approval_request is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Approval request not found",
        )

    if approval_request.status != ApprovalStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only pending approval requests can be approved",
        )

    approval_request.status = ApprovalStatus.APPROVED
    approval_request.reviewed_by = payload.reviewed_by
    approval_request.review_comment = payload.review_comment
    approval_request.reviewed_at = datetime.now(UTC)

    AuditLogService(db).record(
        event_type=AuditEventType.APPROVAL_APPROVED,
        entity_type="approval_request",
        entity_id=str(approval_request.id),
        actor=payload.reviewed_by,
        metadata={
            "review_comment": payload.review_comment,
            "action_type": approval_request.action_type.value,
        },
    )
    db.commit()
    db.refresh(approval_request)

    return approval_request


@router.post("/{approval_request_id}/reject", response_model=ApprovalRequestResponse)
def reject_request(
    approval_request_id: UUID,
    payload: ApprovalReviewRequest,
    db: DbSession,
) -> ApprovalRequest:
    approval_request = db.get(ApprovalRequest, approval_request_id)

    if approval_request is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Approval request not found",
        )

    if approval_request.status != ApprovalStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only pending approval requests can be rejected",
        )

    approval_request.status = ApprovalStatus.REJECTED
    approval_request.reviewed_by = payload.reviewed_by
    approval_request.review_comment = payload.review_comment
    approval_request.reviewed_at = datetime.now(UTC)

    db.commit()
    db.refresh(approval_request)

    AuditLogService(db).record(
        event_type=AuditEventType.APPROVAL_REJECTED,
        entity_type="approval_request",
        entity_id=str(approval_request.id),
        actor=payload.reviewed_by,
        metadata={
            "review_comment": payload.review_comment,
            "action_type": approval_request.action_type.value,
        },
    )
    return approval_request


@router.post("/{approval_request_id}/execute", response_model=ApprovalRequestResponse)
def execute_request(
    approval_request_id: UUID,
    db: DbSession,
) -> ApprovalRequest:
    approval_request = db.get(ApprovalRequest, approval_request_id)

    if approval_request is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Approval request not found",
        )

    execution_service = ApprovalExecutionService()

    try:
        execution_result = execution_service.execute(approval_request)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    approval_request.status = ApprovalStatus.EXECUTED
    approval_request.execution_result = execution_result

    AuditLogService(db).record(
        event_type=AuditEventType.APPROVAL_EXECUTED,
        entity_type="approval_request",
        entity_id=str(approval_request.id),
        actor="system",
        metadata={
            "action_type": approval_request.action_type.value,
            "execution_result": execution_result,
        },
    )
    db.commit()
    db.refresh(approval_request)

    return approval_request
