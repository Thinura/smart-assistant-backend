from uuid import UUID

from sqlalchemy.orm import Session

from app.models.audit_log import AuditEventType
from app.models.candidate_workflow import CandidateWorkflow
from app.schemas.candidate_workflow import CandidateWorkflowCreate
from app.services.audit_log_service import AuditLogService


class CandidateWorkflowService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_workflow(self, payload: CandidateWorkflowCreate) -> CandidateWorkflow:
        workflow = CandidateWorkflow(**payload.model_dump())

        self.db.add(workflow)
        self.db.flush()

        AuditLogService(self.db).record(
            event_type=AuditEventType.CANDIDATE_WORKFLOW_CREATED,
            entity_type="candidate_workflow",
            entity_id=str(workflow.id),
            actor="agent",
            metadata={
                "candidate_id": str(workflow.candidate_id),
                "agent_run_id": str(workflow.agent_run_id) if workflow.agent_run_id else None,
                "workflow_type": workflow.workflow_type.value,
                "status": workflow.status.value,
                "role_name": workflow.role_name,
                "candidate_review_id": str(workflow.candidate_review_id)
                if workflow.candidate_review_id
                else None,
                "candidate_job_match_id": str(workflow.candidate_job_match_id)
                if workflow.candidate_job_match_id
                else None,
                "interview_kit_id": str(workflow.interview_kit_id)
                if workflow.interview_kit_id
                else None,
                "approval_request_id": str(workflow.approval_request_id)
                if workflow.approval_request_id
                else None,
                "score": workflow.score,
                "recommendation": workflow.recommendation,
            },
        )

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
