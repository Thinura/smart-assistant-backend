from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import DbSession
from app.models.agent_run import AgentRun, AgentRunStatus
from app.models.approval_request import ApprovalRequest
from app.models.audit_log import AuditLog
from app.models.tool_call import ToolCall
from app.schemas.agent_run import (
    AgentRunResponse,
    AgentRunTraceResponse,
    AgentRunTraceSummary,
)

STATUS_FILTER_QUERY = Query(default=None, alias="status")
LIMIT_QUERY = Query(default=50, ge=1, le=200)

router = APIRouter()

@router.get("", response_model=list[AgentRunResponse])
def list_agent_runs(
    db: DbSession,
    conversation_id: UUID | None = None,
    status_filter: AgentRunStatus | None = STATUS_FILTER_QUERY,
    limit: int = LIMIT_QUERY,
) -> list[AgentRun]:
    query = db.query(AgentRun)

    if conversation_id is not None:
        query = query.filter(AgentRun.conversation_id == conversation_id)

    if status_filter is not None:
        query = query.filter(AgentRun.status == status_filter)

    return query.order_by(AgentRun.started_at.desc()).limit(limit).all()

@router.get("/{agent_run_id}", response_model=AgentRunResponse)
def get_agent_run(
    agent_run_id: UUID,
    db: DbSession,
) -> AgentRun:
    agent_run = db.get(AgentRun, agent_run_id)

    if agent_run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent run not found",
        )

    return agent_run


@router.get("/{agent_run_id}/trace", response_model=AgentRunTraceResponse)
def get_agent_run_trace(
    agent_run_id: UUID,
    db: DbSession,
) -> AgentRunTraceResponse:
    agent_run = db.get(AgentRun, agent_run_id)

    if agent_run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent run not found",
        )

    tool_calls = (
        db.query(ToolCall)
        .filter(ToolCall.agent_run_id == agent_run_id)
        .order_by(ToolCall.created_at.asc())
        .all()
    )

    approval_requests = (
        db.query(ApprovalRequest)
        .filter(ApprovalRequest.agent_run_id == agent_run_id)
        .order_by(ApprovalRequest.created_at.asc())
        .all()
    )

    audit_logs = (
        db.query(AuditLog)
        .filter(
            AuditLog.event_metadata["agent_run_id"].astext == str(agent_run_id),
        )
        .order_by(AuditLog.created_at.asc())
        .all()
    )

    run_metadata = agent_run.run_metadata or {}

    summary = AgentRunTraceSummary(
        agent_run_id=agent_run.id,
        status=agent_run.status,
        intent=run_metadata.get("intent"),
        tool_call_count=len(tool_calls),
        approval_request_count=len(approval_requests),
        audit_log_count=len(audit_logs),
        has_error=agent_run.error_message is not None
        or any(not tool_call.success for tool_call in tool_calls),
    )

    return AgentRunTraceResponse(
        summary=summary,
        agent_run=agent_run,
        tool_calls=tool_calls,
        approval_requests=approval_requests,
        audit_logs=audit_logs,
    )
