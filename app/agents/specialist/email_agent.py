from app.agents.nodes import handle_email_draft
from app.agents.state import AgentState


def email_agent(state: AgentState) -> AgentState:
    return handle_email_draft(state)
