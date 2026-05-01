from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import DbSession
from app.models.agent_run import AgentRun
from app.models.approval_request import ApprovalRequest, ApprovalStatus
from app.models.audit_log import AuditEventType, AuditLog
from app.models.candidate import Candidate, CandidateStatus
from app.models.candidate_review import CandidateReview
from app.models.document import Document, DocumentType
from app.models.outbox_message import OutboxMessage, OutboxMessageStatus
from app.schemas.candidate import (
    CandidateCreate,
    CandidateResponse,
    CandidateStatusUpdate,
    CandidateTimelineResponse,
    CandidateTimelineSummary,
    CandidateUpdate,
)
from app.schemas.candidate_review import CandidateReviewResponse
from app.services.audit_log_service import AuditLogService

router = APIRouter()

STATUS_QUERY = Query(default=None, alias="status")
ROLE_QUERY = Query(default=None, alias="role")
SEARCH_QUERY = Query(default=None, alias="search")
LIMIT_QUERY = Query(default=100, ge=1, le=500)


@router.post("", response_model=CandidateResponse, status_code=status.HTTP_201_CREATED)
def create_candidate(
    payload: CandidateCreate,
    db: DbSession,
) -> Candidate:
    if payload.cv_document_id is not None:
        document = db.get(Document, payload.cv_document_id)

        if document is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="CV document not found",
            )

        if document.document_type != DocumentType.CV:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Linked document must be of type cv",
            )

    candidate = Candidate(**payload.model_dump())

    db.add(candidate)
    db.flush()

    AuditLogService(db).record(
        event_type=AuditEventType.CANDIDATE_CREATED,
        entity_type="candidate",
        entity_id=str(candidate.id),
        actor="system",
        metadata={
            "full_name": candidate.full_name,
            "email": candidate.email,
            "role_applied_for": candidate.role_applied_for,
            "status": candidate.status.value,
            "cv_document_id": str(candidate.cv_document_id) if candidate.cv_document_id else None,
        },
    )
    db.commit()
    db.refresh(candidate)

    return candidate


@router.get("", response_model=list[CandidateResponse])
def list_candidates(
    db: DbSession,
    status_filter: CandidateStatus | None = STATUS_QUERY,
    role_filter: str | None = ROLE_QUERY,
    search: str | None = SEARCH_QUERY,
    limit: int = LIMIT_QUERY,
) -> list[Candidate]:
    query = db.query(Candidate)

    if status_filter is not None:
        query = query.filter(Candidate.status == status_filter)

    if role_filter is not None:
        query = query.filter(Candidate.role_applied_for.ilike(f"%{role_filter}%"))

    if search is not None:
        search_pattern = f"%{search}%"
        query = query.filter(
            Candidate.full_name.ilike(search_pattern)
            | Candidate.email.ilike(search_pattern)
            | Candidate.role_applied_for.ilike(search_pattern)
        )

    return query.order_by(Candidate.created_at.desc()).limit(limit).all()


@router.get("/{candidate_id}", response_model=CandidateResponse)
def get_candidate(
    candidate_id: UUID,
    db: DbSession,
) -> Candidate:
    candidate = db.get(Candidate, candidate_id)

    if candidate is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate not found",
        )

    return candidate


@router.post("/{candidate_id}/status", response_model=CandidateResponse)
def update_candidate_status(
    candidate_id: UUID,
    payload: CandidateStatusUpdate,
    db: DbSession,
) -> Candidate:
    candidate = db.get(Candidate, candidate_id)

    if candidate is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate not found",
        )

    previous_status = candidate.status
    candidate.status = payload.status

    db.flush()

    AuditLogService(db).record(
        event_type=AuditEventType.CANDIDATE_UPDATED,
        entity_type="candidate",
        entity_id=str(candidate.id),
        actor=payload.updated_by,
        metadata={
            "updated_fields": ["status"],
            "previous_status": previous_status.value,
            "new_status": candidate.status.value,
            "reason": payload.reason,
        },
    )

    db.commit()
    db.refresh(candidate)

    return candidate


@router.get("/{candidate_id}/timeline", response_model=CandidateTimelineResponse)
def get_candidate_timeline(
    candidate_id: UUID,
    db: DbSession,
) -> CandidateTimelineResponse:
    candidate = db.get(Candidate, candidate_id)

    if candidate is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate not found",
        )

    candidate_id_text = str(candidate.id)

    cv_document = None
    if candidate.cv_document_id is not None:
        cv_document = db.get(Document, candidate.cv_document_id)

    audit_logs = (
        db.query(AuditLog)
        .filter(
            AuditLog.entity_type == "candidate",
            AuditLog.entity_id == candidate_id_text,
        )
        .order_by(AuditLog.created_at.asc())
        .all()
    )

    agent_runs = (
        db.query(AgentRun)
        .filter(AgentRun.run_metadata["sources"].astext.contains(candidate_id_text))
        .order_by(AgentRun.started_at.asc())
        .all()
    )

    approval_requests = (
        db.query(ApprovalRequest)
        .filter(ApprovalRequest.action_payload["candidate_id"].astext == candidate_id_text)
        .order_by(ApprovalRequest.created_at.asc())
        .all()
    )

    outbox_messages = (
        db.query(OutboxMessage)
        .filter(OutboxMessage.candidate_id == candidate.id)
        .order_by(OutboxMessage.created_at.asc())
        .all()
    )

    candidate_reviews = (
        db.query(CandidateReview)
        .filter(CandidateReview.candidate_id == candidate.id)
        .order_by(CandidateReview.created_at.desc())
        .all()
    )

    latest_review = candidate_reviews[0] if candidate_reviews else None

    summary = CandidateTimelineSummary(
        candidate_id=candidate.id,
        has_cv=candidate.cv_document_id is not None,
        audit_log_count=len(audit_logs),
        agent_run_count=len(agent_runs),
        approval_request_count=len(approval_requests),
        pending_approval_count=sum(
            1
            for approval_request in approval_requests
            if approval_request.status == ApprovalStatus.PENDING
        ),
        outbox_message_count=len(outbox_messages),
        sent_outbox_message_count=sum(
            1
            for outbox_message in outbox_messages
            if outbox_message.status == OutboxMessageStatus.SENT
        ),
        candidate_review_count=len(candidate_reviews),
        latest_review_score=latest_review.score if latest_review else None,
        latest_review_recommendation=latest_review.recommendation if latest_review else None,
    )

    return CandidateTimelineResponse(
        summary=summary,
        candidate=candidate,
        cv_document=cv_document,
        audit_logs=audit_logs,
        agent_runs=agent_runs,
        approval_requests=approval_requests,
        outbox_messages=outbox_messages,
        candidate_reviews=candidate_reviews,
    )


@router.get("/{candidate_id}/reviews", response_model=list[CandidateReviewResponse])
def list_candidate_reviews(
    candidate_id: UUID,
    db: DbSession,
) -> list[CandidateReview]:
    candidate = db.get(Candidate, candidate_id)

    if candidate is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate not found",
        )

    return (
        db.query(CandidateReview)
        .filter(CandidateReview.candidate_id == candidate_id)
        .order_by(CandidateReview.created_at.desc())
        .all()
    )


@router.patch("/{candidate_id}", response_model=CandidateResponse)
def update_candidate(
    candidate_id: UUID,
    payload: CandidateUpdate,
    db: DbSession,
) -> Candidate:
    candidate = db.get(Candidate, candidate_id)

    if candidate is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate not found",
        )

    previous_status = candidate.status.value
    previous_cv_document_id = str(candidate.cv_document_id) if candidate.cv_document_id else None
    update_data = payload.model_dump(exclude_unset=True)

    if "cv_document_id" in update_data and update_data["cv_document_id"] is not None:
        document = db.get(Document, update_data["cv_document_id"])

        if document is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="CV document not found",
            )

        if document.document_type != DocumentType.CV:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Linked document must be of type cv",
            )

    for field, value in update_data.items():
        setattr(candidate, field, value)

    db.flush()
    AuditLogService(db).record(
        event_type=AuditEventType.CANDIDATE_UPDATED,
        entity_type="candidate",
        entity_id=str(candidate.id),
        actor="system",
        metadata={
            "updated_fields": list(update_data.keys()),
            "previous_status": previous_status,
            "new_status": candidate.status.value,
            "previous_cv_document_id": previous_cv_document_id,
            "new_cv_document_id": str(candidate.cv_document_id)
            if candidate.cv_document_id
            else None,
        },
    )
    db.commit()
    db.refresh(candidate)

    return candidate
