from app.agents.nodes import handle_document_qa
from app.agents.state import AgentState


def document_agent(state: AgentState) -> AgentState:
    return handle_document_qa(state)
