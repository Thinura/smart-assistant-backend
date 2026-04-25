from app.agents.state import AgentState
from app.services.llm_service import LLMService


def generate_assistant_response(state: AgentState) -> AgentState:
    prompt = f"""
You are Smart Assistant, a helpful AI assistant for agentic AI and recruitment workflows.
Answer clearly and concisely.

User message:
{state["user_message"]}
"""

    llm_service = LLMService()
    assistant_message = llm_service.generate_response(prompt)

    return {
        **state,
        "assistant_message": assistant_message,
    }
