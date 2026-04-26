from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.intents import get_intent_classifier_prompt, normalize_intent
from app.agents.state import AgentState
from app.services.chat_model_service import get_chat_model
from app.services.tool_execution_service import ToolExecutionService


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
    from app.db.session import SessionLocal

    db = SessionLocal()

    try:
        tool_execution_service = ToolExecutionService(db)

        result, tool_call = tool_execution_service.run_tool(
            tool_name="conversation_summary",
            payload={
                "conversation_id": str(state["conversation_id"]),
            },
            agent_run_id=state.get("agent_run_id"),
        )

        tool_result = {
            "tool_name": "conversation_summary",
            "tool_call_id": str(tool_call.id),
            "success": result.success,
            "data": result.data,
            "error": result.error,
        }

        existing_tool_results = state.get("tool_results", [])

        return {
            **state,
            "tool_results": [*existing_tool_results, tool_result],
            "assistant_message": (
                "Document Q&A is not connected yet, but the LangGraph node successfully "
                "called the tool registry and logged the tool execution."
            ),
        }

    finally:
        db.close()


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
