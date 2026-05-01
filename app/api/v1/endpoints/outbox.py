from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import DbSession
from app.models.outbox_message import OutboxMessage, OutboxMessageStatus
from app.schemas.outbox_message import (
    OutboxBulkSendRequest,
    OutboxBulkSendResponse,
    OutboxMarkSentRequest,
    OutboxMessageResponse,
    OutboxSummaryResponse,
)
from app.services.outbox_send_service import OutboxSendService
from app.services.outbox_service import OutboxService

router = APIRouter()

StatusQuery = Annotated[
    OutboxMessageStatus | None,
    Query(alias="status"),
]

LimitQuery = Annotated[
    int,
    Query(ge=1, le=500),
]


@router.get("", response_model=list[OutboxMessageResponse])
def list_outbox_messages(
    db: DbSession,
    status_filter: StatusQuery = None,
    limit: LimitQuery = 100,
) -> list[OutboxMessage]:
    query = db.query(OutboxMessage)

    if status_filter is not None:
        query = query.filter(OutboxMessage.status == status_filter)

    return query.order_by(OutboxMessage.created_at.desc()).limit(limit).all()


@router.post("/send-pending", response_model=OutboxBulkSendResponse)
def send_pending_outbox_messages(
    payload: OutboxBulkSendRequest,
    db: DbSession,
) -> dict:
    return OutboxSendService(db).send_pending(
        limit=payload.limit,
        include_failed=payload.include_failed,
    )


@router.get("/summary", response_model=OutboxSummaryResponse)
def get_outbox_summary(
    db: DbSession,
) -> dict:
    return OutboxSendService(db).get_summary()


@router.post("/{outbox_message_id}/send", response_model=OutboxMessageResponse)
def send_outbox_message(
    outbox_message_id: UUID,
    db: DbSession,
) -> OutboxMessage:
    try:
        return OutboxSendService(db).send(outbox_message_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.get("/{message_id}", response_model=OutboxMessageResponse)
def get_outbox_message(
    message_id: UUID,
    db: DbSession,
) -> OutboxMessage:
    outbox_message = db.get(OutboxMessage, message_id)

    if outbox_message is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Outbox message not found",
        )

    return outbox_message


@router.post("/{message_id}/mark-sent", response_model=OutboxMessageResponse)
def mark_outbox_message_sent(
    message_id: UUID,
    payload: OutboxMarkSentRequest,
    db: DbSession,
) -> OutboxMessage:
    outbox_message = db.get(OutboxMessage, message_id)

    if outbox_message is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Outbox message not found",
        )

    if outbox_message.status == OutboxMessageStatus.SENT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Outbox message is already marked as sent",
        )

    outbox_message = OutboxService(db).mark_sent(
        outbox_message=outbox_message,
        provider_message_id=payload.provider_message_id,
    )

    db.commit()
    db.refresh(outbox_message)

    return outbox_message
