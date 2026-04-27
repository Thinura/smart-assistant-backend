from uuid import UUID

from fastapi import APIRouter, HTTPException, status

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
) -> ConversationTraceResponse:
    conversation = db.get(Conversation, conversation_id)

    if conversation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    messages = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
        .all()
    )

    agent_runs = (
        db.query(AgentRun)
        .filter(AgentRun.conversation_id == conversation_id)
        .order_by(AgentRun.started_at.asc())
        .all()
    )

    agent_run_ids = [agent_run.id for agent_run in agent_runs]

    tool_calls = []
    approval_requests = []

    if agent_run_ids:
        tool_calls = (
            db.query(ToolCall)
            .filter(ToolCall.agent_run_id.in_(agent_run_ids))
            .order_by(ToolCall.created_at.asc())
            .all()
        )

        approval_requests = (
            db.query(ApprovalRequest)
            .filter(ApprovalRequest.agent_run_id.in_(agent_run_ids))
            .order_by(ApprovalRequest.created_at.asc())
            .all()
        )

    summary = ConversationTraceSummary(
        conversation_id=conversation.id,
        message_count=len(messages),
        agent_run_count=len(agent_runs),
        tool_call_count=len(tool_calls),
        approval_request_count=len(approval_requests),
        pending_approval_count=sum(
            1
            for approval_request in approval_requests
            if approval_request.status == ApprovalStatus.PENDING
        ),
        has_failed_run=any(agent_run.status == AgentRunStatus.FAILED for agent_run in agent_runs),
    )

    return ConversationTraceResponse(
        summary=summary,
        conversation=conversation,
        messages=messages,
        agent_runs=agent_runs,
        tool_calls=tool_calls,
        approval_requests=approval_requests,
    )
