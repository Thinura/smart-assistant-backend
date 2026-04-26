from langgraph.graph import END, StateGraph

from app.agents.intents import AgentIntent
from app.agents.nodes import classify_intent
from app.agents.registry import INTENT_NODE_REGISTRY
from app.agents.state import AgentState


def route_by_intent(state: AgentState) -> str:
    return state["intent"].value


def detect_intent_by_rules(message: str) -> AgentIntent | None:
    normalized_message = message.strip().lower()

    document_keywords = [
        "uploaded document",
        "uploaded file",
        "from the document",
        "from uploaded document",
        "according to the document",
        "according to uploaded document",
        "based on the document",
        "based on uploaded document",
        "policy document",
        "document says",
        "file says",
        "pdf",
        "docx",
    ]

    candidate_keywords = [
        "review this cv",
        "review cv",
        "candidate review",
        "review this candidate",
        "match this candidate",
        "match candidate",
        "jd match",
        "job description match",
        "resume review",
        "assignment review",
    ]

    email_keywords = [
        "draft email",
        "write email",
        "email draft",
        "rejection email",
        "shortlist email",
        "interview invite",
        "follow-up email",
        "candidate email",
    ]

    if any(keyword in normalized_message for keyword in document_keywords):
        return AgentIntent.DOCUMENT_QA

    if any(keyword in normalized_message for keyword in candidate_keywords):
        return AgentIntent.CANDIDATE_REVIEW

    if any(keyword in normalized_message for keyword in email_keywords):
        return AgentIntent.EMAIL_DRAFT

    return None


def build_chat_graph():
    graph = StateGraph(AgentState)

    graph.add_node("classify_intent", classify_intent)

    for intent, node in INTENT_NODE_REGISTRY.items():
        graph.add_node(intent.value, node)

    graph.set_entry_point("classify_intent")

    graph.add_conditional_edges(
        "classify_intent",
        route_by_intent,
        {intent.value: intent.value for intent in INTENT_NODE_REGISTRY},
    )

    for intent in INTENT_NODE_REGISTRY:
        graph.add_edge(intent.value, END)

    return graph.compile()


chat_graph = build_chat_graph()
