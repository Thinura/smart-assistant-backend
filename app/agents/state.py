from typing import Any, TypedDict
from uuid import UUID

from sqlalchemy.orm import Session


class AgentState(TypedDict, total=False):
    conversation_id: UUID
    agent_run_id: UUID
    user_message: str
    db: Session

    intent: str
    selected_agent: str

    assistant_message: str
    sources: list[dict[str, Any]]
    tool_results: list[dict[str, Any]]

    candidate_id: str | None
    document_type: str | None
    email_type: str | None

    extracted_variables: dict[str, Any]
