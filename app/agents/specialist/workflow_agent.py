from app.agents.nodes import handle_interview_workflow
from app.agents.state import AgentState


def workflow_agent(state: AgentState) -> AgentState:
    return handle_interview_workflow(state)
