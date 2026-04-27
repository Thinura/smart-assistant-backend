from collections.abc import Callable

from app.agents.intents import AgentIntent
from app.agents.nodes import (
    generate_general_response,
    handle_candidate_review,
    handle_document_qa,
    handle_email_draft_placeholder,
    handle_unknown_intent,
)
from app.agents.state import AgentState

AgentNode = Callable[[AgentState], AgentState]


INTENT_NODE_REGISTRY: dict[AgentIntent, AgentNode] = {
    AgentIntent.GENERAL_CHAT: generate_general_response,
    AgentIntent.DOCUMENT_QA: handle_document_qa,
    AgentIntent.CANDIDATE_REVIEW: handle_candidate_review,
    AgentIntent.EMAIL_DRAFT: handle_email_draft_placeholder,
    AgentIntent.UNKNOWN: handle_unknown_intent,
}
