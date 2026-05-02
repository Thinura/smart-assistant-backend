from app.agents.nodes import generate_general_response
from app.agents.state import AgentState


def general_agent(state: AgentState) -> AgentState:
    return generate_general_response(state)
