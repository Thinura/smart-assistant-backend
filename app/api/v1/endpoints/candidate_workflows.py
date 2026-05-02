from uuid import UUID

from fastapi import APIRouter

from app.api.deps import DbSession
from app.models.candidate_workflow import CandidateWorkflow
from app.schemas.candidate_workflow import CandidateWorkflowResponse
from app.services.candidate_workflow_service import CandidateWorkflowService

router = APIRouter()


@router.get(
    "/candidates/{candidate_id}/workflows",
    response_model=list[CandidateWorkflowResponse],
)
def list_candidate_workflows(
    candidate_id: UUID,
    db: DbSession,
) -> list[CandidateWorkflow]:
    return CandidateWorkflowService(db).list_for_candidate(candidate_id)
