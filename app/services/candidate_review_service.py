from sqlalchemy.orm import Session

from app.models.audit_log import AuditEventType
from app.models.candidate_review import CandidateReview
from app.schemas.candidate_review import CandidateReviewCreate
from app.services.audit_log_service import AuditLogService


class CandidateReviewService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_review(self, payload: CandidateReviewCreate) -> CandidateReview:
        review = CandidateReview(**payload.model_dump())

        self.db.add(review)
        self.db.flush()

        AuditLogService(self.db).record(
            event_type=AuditEventType.CANDIDATE_REVIEW_CREATED,
            entity_type="candidate_review",
            entity_id=str(review.id),
            actor="agent",
            metadata={
                "candidate_id": str(review.candidate_id),
                "agent_run_id": str(review.agent_run_id) if review.agent_run_id else None,
                "cv_document_id": str(review.cv_document_id) if review.cv_document_id else None,
                "score": review.score,
                "recommendation": review.recommendation.value,
                "confidence": review.confidence.value,
            },
        )

        return review
