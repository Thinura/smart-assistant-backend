from app.agents.nodes import handle_candidate_review
from app.agents.state import AgentState


def candidate_agent(state: AgentState) -> AgentState:
    return handle_candidate_review(state)
