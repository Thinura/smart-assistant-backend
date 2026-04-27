from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.api.deps import DbSession
from app.models.audit_log import AuditEventType
from app.models.candidate import Candidate
from app.models.document import Document, DocumentType
from app.schemas.candidate import CandidateCreate, CandidateResponse, CandidateUpdate
from app.services.audit_log_service import AuditLogService

router = APIRouter()


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
) -> list[Candidate]:
    return db.query(Candidate).order_by(Candidate.created_at.desc()).all()


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
