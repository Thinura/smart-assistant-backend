from uuid import UUID

from sqlalchemy.orm import Session

from app.models.candidate_workflow import CandidateWorkflow
from app.schemas.candidate_workflow import CandidateWorkflowCreate


class CandidateWorkflowService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_workflow(self, payload: CandidateWorkflowCreate) -> CandidateWorkflow:
        workflow = CandidateWorkflow(**payload.model_dump())

        self.db.add(workflow)
        self.db.flush()
        self.db.commit()
        self.db.refresh(workflow)

        return workflow

    def list_for_candidate(self, candidate_id: UUID) -> list[CandidateWorkflow]:
        return (
            self.db.query(CandidateWorkflow)
            .filter(CandidateWorkflow.candidate_id == candidate_id)
            .order_by(CandidateWorkflow.created_at.desc())
            .all()
        )
