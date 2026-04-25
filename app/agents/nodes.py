from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.intents import get_intent_classifier_prompt, normalize_intent
from app.agents.state import AgentState
from app.services.chat_model_service import get_chat_model


def classify_intent(state: AgentState) -> AgentState:
    model = get_chat_model()

    messages = [
        SystemMessage(content=get_intent_classifier_prompt()),
        HumanMessage(content=state["user_message"]),
    ]

    response = model.invoke(messages)
    intent = normalize_intent(str(response.content))

    return {
        **state,
        "intent": intent,
    }


def generate_general_response(state: AgentState) -> AgentState:
    model = get_chat_model()

    messages = [
        SystemMessage(
            content=(
                "You are Smart Assistant, a helpful AI assistant for agentic AI, "
                "HR, recruitment, and productivity workflows. "
                "Answer clearly and concisely."
            )
        ),
        HumanMessage(content=state["user_message"]),
    ]

    response = model.invoke(messages)

    return {
        **state,
        "assistant_message": str(response.content).strip(),
    }


def handle_document_qa_placeholder(state: AgentState) -> AgentState:
    return {
        **state,
        "assistant_message": (
            "Document Q&A is not connected yet. Next we will add document upload, "
            "chunking, embeddings, and retrieval."
        ),
    }


def handle_candidate_review_placeholder(state: AgentState) -> AgentState:
    return {
        **state,
        "assistant_message": (
            "Candidate review is not connected yet. Next we will add candidate profiles, "
            "CV parsing, assignment review, and JD matching."
        ),
    }


def handle_email_draft_placeholder(state: AgentState) -> AgentState:
    return {
        **state,
        "assistant_message": (
            "Email drafting is not connected yet. Later this will create a draft and "
            "send it for human approval before any email is sent."
        ),
    }


def handle_unknown_intent(state: AgentState) -> AgentState:
    return {
        **state,
        "assistant_message": (
            "I could not clearly understand the request. "
            "Please ask again with a little more context."
        ),
    }
