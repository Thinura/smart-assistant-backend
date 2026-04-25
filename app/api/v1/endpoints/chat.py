from fastapi import APIRouter, HTTPException, status

from app.api.deps import DbSession
from app.models.conversation import Conversation
from app.models.message import Message, MessageRole
from app.schemas.chat import ChatRequest, ChatResponse

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

    user_message = Message(
        conversation_id=payload.conversation_id,
        role=MessageRole.USER,
        content=payload.message,
    )

    assistant_text = f"Received your message: {payload.message}"

    assistant_message = Message(
        conversation_id=payload.conversation_id,
        role=MessageRole.ASSISTANT,
        content=assistant_text,
    )

    db.add(user_message)
    db.add(assistant_message)
    db.commit()

    return ChatResponse(
        conversation_id=payload.conversation_id,
        user_message=payload.message,
        assistant_message=assistant_text,
    )