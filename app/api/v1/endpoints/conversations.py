from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import DbSession
from app.models.agent_run import AgentRun, AgentRunStatus
from app.models.approval_request import ApprovalRequest, ApprovalStatus
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.tool_call import ToolCall
from app.schemas.conversation import (
    ConversationCreate,
    ConversationResponse,
    ConversationTraceResponse,
    ConversationTraceSummary,
)
from app.schemas.message import MessageResponse

router = APIRouter()


@router.post(
    "",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_conversation(
    payload: ConversationCreate,
    db: DbSession,
) -> Conversation:
    conversation = Conversation(title=payload.title)

    db.add(conversation)
    db.commit()
    db.refresh(conversation)

    return conversation


@router.get("", response_model=list[ConversationResponse])
def list_conversations(
    db: DbSession,
) -> list[Conversation]:
    return db.query(Conversation).order_by(Conversation.created_at.desc()).all()


@router.get("/{conversation_id}/messages", response_model=list[MessageResponse])
def list_conversation_messages(
    conversation_id: str,
    db: DbSession,
) -> list[Message]:

    conversation = db.get(Conversation, conversation_id)

    if conversation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    return (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
        .all()
    )


@router.get("/{conversation_id}/trace", response_model=ConversationTraceResponse)
def get_conversation_trace(
    conversation_id: UUID,
    db: DbSession,
    limit: int = Query(default=50, ge=1, le=200),
    include_messages: bool = True,
    include_agent_runs: bool = True,
    include_tool_calls: bool = True,
    include_approvals: bool = True,
) -> ConversationTraceResponse:
    conversation = db.get(Conversation, conversation_id)

    if conversation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    all_agent_runs = (
        db.query(AgentRun)
        .filter(AgentRun.conversation_id == conversation_id)
        .order_by(AgentRun.started_at.asc())
        .all()
    )

    agent_run_ids = [agent_run.id for agent_run in all_agent_runs]

    message_count = db.query(Message).filter(Message.conversation_id == conversation_id).count()

    tool_call_count = 0
    approval_request_count = 0
    pending_approval_count = 0

    if agent_run_ids:
        tool_call_count = (
            db.query(ToolCall).filter(ToolCall.agent_run_id.in_(agent_run_ids)).count()
        )

        approval_request_count = (
            db.query(ApprovalRequest)
            .filter(ApprovalRequest.agent_run_id.in_(agent_run_ids))
            .count()
        )

        pending_approval_count = (
            db.query(ApprovalRequest)
            .filter(
                ApprovalRequest.agent_run_id.in_(agent_run_ids),
                ApprovalRequest.status == ApprovalStatus.PENDING,
            )
            .count()
        )

    messages = []
    if include_messages:
        messages = (
            db.query(Message)
            .filter(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc())
            .limit(limit)
            .all()
        )
        messages.reverse()

    agent_runs = []
    visible_agent_run_ids = agent_run_ids

    if include_agent_runs:
        agent_runs = (
            db.query(AgentRun)
            .filter(AgentRun.conversation_id == conversation_id)
            .order_by(AgentRun.started_at.desc())
            .limit(limit)
            .all()
        )
        agent_runs.reverse()
        visible_agent_run_ids = [agent_run.id for agent_run in agent_runs]

    tool_calls = []
    if include_tool_calls and visible_agent_run_ids:
        tool_calls = (
            db.query(ToolCall)
            .filter(ToolCall.agent_run_id.in_(visible_agent_run_ids))
            .order_by(ToolCall.created_at.asc())
            .all()
        )

    approval_requests = []
    if include_approvals and visible_agent_run_ids:
        approval_requests = (
            db.query(ApprovalRequest)
            .filter(ApprovalRequest.agent_run_id.in_(visible_agent_run_ids))
            .order_by(ApprovalRequest.created_at.asc())
            .all()
        )

    summary = ConversationTraceSummary(
        conversation_id=conversation.id,
        message_count=message_count,
        agent_run_count=len(all_agent_runs),
        tool_call_count=tool_call_count,
        approval_request_count=approval_request_count,
        pending_approval_count=pending_approval_count,
        has_failed_run=any(
            agent_run.status == AgentRunStatus.FAILED for agent_run in all_agent_runs
        ),
    )

    return ConversationTraceResponse(
        summary=summary,
        conversation=conversation,
        messages=messages,
        agent_runs=agent_runs,
        tool_calls=tool_calls,
        approval_requests=approval_requests,
    )
