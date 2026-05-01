from fastapi import APIRouter

from app.api.deps import DbSession
from app.models.agent_run import AgentRun, AgentRunStatus
from app.models.approval_request import ApprovalRequest, ApprovalStatus
from app.models.candidate import Candidate
from app.models.candidate_review import CandidateReview
from app.models.document import Document
from app.models.outbox_message import OutboxMessage, OutboxMessageStatus
from app.schemas.dashboard import DashboardSummaryResponse

router = APIRouter()


@router.get("/summary", response_model=DashboardSummaryResponse)
def get_dashboard_summary(db: DbSession) -> DashboardSummaryResponse:
    candidate_count = db.query(Candidate).count()
    document_count = db.query(Document).count()
    candidate_review_count = db.query(CandidateReview).count()

    approval_request_count = db.query(ApprovalRequest).count()
    pending_approval_count = (
        db.query(ApprovalRequest).filter(ApprovalRequest.status == ApprovalStatus.PENDING).count()
    )

    outbox_message_count = db.query(OutboxMessage).count()
    pending_outbox_count = (
        db.query(OutboxMessage).filter(OutboxMessage.status == OutboxMessageStatus.PENDING).count()
    )
    sent_outbox_count = (
        db.query(OutboxMessage).filter(OutboxMessage.status == OutboxMessageStatus.SENT).count()
    )

    agent_run_count = db.query(AgentRun).count()
    failed_agent_run_count = (
        db.query(AgentRun).filter(AgentRun.status == AgentRunStatus.FAILED).count()
    )

    return DashboardSummaryResponse(
        candidate_count=candidate_count,
        document_count=document_count,
        candidate_review_count=candidate_review_count,
        approval_request_count=approval_request_count,
        pending_approval_count=pending_approval_count,
        outbox_message_count=outbox_message_count,
        pending_outbox_count=pending_outbox_count,
        sent_outbox_count=sent_outbox_count,
        agent_run_count=agent_run_count,
        failed_agent_run_count=failed_agent_run_count,
    )
