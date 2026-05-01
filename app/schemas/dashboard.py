from pydantic import BaseModel


class DashboardSummaryResponse(BaseModel):
    candidate_count: int
    document_count: int
    candidate_review_count: int
    approval_request_count: int
    pending_approval_count: int
    outbox_message_count: int
    pending_outbox_count: int
    sent_outbox_count: int
    agent_run_count: int
    failed_agent_run_count: int
