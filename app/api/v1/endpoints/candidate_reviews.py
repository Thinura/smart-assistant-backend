from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.api.deps import DbSession
from app.models.candidate_review import CandidateReview
from app.schemas.candidate_review import CandidateReviewResponse

router = APIRouter()


@router.get("/{review_id}", response_model=CandidateReviewResponse)
def get_candidate_review(
    review_id: UUID,
    db: DbSession,
) -> CandidateReview:
    review = db.get(CandidateReview, review_id)

    if review is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate review not found",
        )

    return review
