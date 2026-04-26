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
            tool_name="search_documents",
            payload={
                "query": state["user_message"],
                "top_k": 3,
            },
            agent_run_id=state.get("agent_run_id"),
        )

        tool_result = {
            "tool_name": "search_documents",
            "tool_call_id": str(tool_call.id),
            "success": result.success,
            "data": result.data,
            "error": result.error,
        }

        existing_tool_results = state.get("tool_results", [])

        if not result.success or result.data is None:
            return {
                **state,
                "tool_results": [*existing_tool_results, tool_result],
                "assistant_message": ("I could not search the uploaded documents right now."),
            }

        results = result.data.get("results", [])

        if not results:
            return {
                **state,
                "tool_results": [*existing_tool_results, tool_result],
                "assistant_message": (
                    "I could not find relevant information in the uploaded documents."
                ),
            }

        context = "\n\n".join(
            f"Source: {item['source']}\nContent: {item['content']}" for item in results
        )

        model = get_chat_model()

        messages = [
            SystemMessage(
                content=(
                    "You are Smart Assistant. Answer the user's question using only "
                    "the provided document context. If the answer is not in the context, "
                    "say you could not find it in the uploaded documents."
                )
            ),
            HumanMessage(
                content=(f"Document context:\n{context}\n\nUser question:\n{state['user_message']}")
            ),
        ]

        response = model.invoke(messages)

        return {
            **state,
            "tool_results": [*existing_tool_results, tool_result],
            "assistant_message": str(response.content).strip(),
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
