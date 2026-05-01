from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.api.deps import DbSession
from app.models.interview_kit import InterviewKit
from app.schemas.interview_kit import InterviewKitResponse

router = APIRouter()


@router.get("/{interview_kit_id}", response_model=InterviewKitResponse)
def get_interview_kit(
    interview_kit_id: UUID,
    db: DbSession,
) -> InterviewKit:
    interview_kit = db.get(InterviewKit, interview_kit_id)

    if interview_kit is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview kit not found",
        )

    return interview_kit
