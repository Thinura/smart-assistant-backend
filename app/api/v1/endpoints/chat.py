from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, status

from app.api.deps import DbSession
from app.models.agent_run import AgentRun, AgentRunStatus
from app.models.conversation import Conversation
from app.models.message import Message, MessageRole
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.llm_service import LLMService

router = APIRouter()


@router.post("", response_model=ChatResponse, status_code=status.HTTP_201_CREATED)
def create_chat_message(
    payload: ChatRequest,
    db: DbSession,
) -> ChatResponse:
    conversation = db.get(Conversation, payload.conversation_id)

    if conversation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    agent_run = AgentRun(
        conversation_id=payload.conversation_id,
        status=AgentRunStatus.RUNNING,
        input_message=payload.message,
        run_metadata={
            "provider": "ollama",
            "mode": "chat",
        },
    )

    db.add(agent_run)
    db.commit()
    db.refresh(agent_run)

    try:
        prompt = f"""
You are Smart Assistant, a helpful AI assistant for agentic AI and recruitment workflows.
Answer clearly and concisely.

User message:
{payload.message}
"""

        llm_service = LLMService()
        assistant_text = llm_service.generate_response(prompt)

        user_message = Message(
            conversation_id=payload.conversation_id,
            role=MessageRole.USER,
            content=payload.message,
        )

        assistant_message = Message(
            conversation_id=payload.conversation_id,
            role=MessageRole.ASSISTANT,
            content=assistant_text,
        )

        agent_run.status = AgentRunStatus.COMPLETED
        agent_run.output_message = assistant_text
        agent_run.completed_at = datetime.now(UTC)

        db.add(user_message)
        db.add(assistant_message)
        db.commit()

        return ChatResponse(
            conversation_id=payload.conversation_id,
            agent_run_id=agent_run.id,
            user_message=payload.message,
            assistant_message=assistant_text,
        )

    except Exception as exc:
        agent_run.status = AgentRunStatus.FAILED
        agent_run.error_message = str(exc)
        agent_run.completed_at = datetime.now(UTC)

        db.commit()

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to generate assistant response",
        ) from exc
