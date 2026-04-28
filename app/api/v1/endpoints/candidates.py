from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import DbSession
from app.models.audit_log import AuditEventType
from app.models.candidate import Candidate, CandidateStatus
from app.models.document import Document, DocumentType
from app.schemas.candidate import (
    CandidateCreate,
    CandidateResponse,
    CandidateUpdate,
)
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
