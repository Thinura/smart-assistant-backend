from fastapi import APIRouter, HTTPException, status

from app.api.deps import DbSession
from app.models.conversation import Conversation
from app.models.message import Message
from app.schemas.conversation import ConversationCreate, ConversationResponse
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