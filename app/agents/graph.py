from langgraph.graph import END, StateGraph

from app.agents.specialist.candidate_agent import candidate_agent
from app.agents.specialist.document_agent import document_agent
from app.agents.specialist.email_agent import email_agent
from app.agents.specialist.general_agent import general_agent
from app.agents.state import AgentState
from app.agents.supervisor import supervisor_agent


def route_to_specialist(state: AgentState) -> str:
    return state.get("selected_agent", "general_agent")


workflow = StateGraph(AgentState)

workflow.add_node("supervisor", supervisor_agent)
workflow.add_node("candidate_agent", candidate_agent)
workflow.add_node("document_agent", document_agent)
workflow.add_node("email_agent", email_agent)
workflow.add_node("general_agent", general_agent)

workflow.set_entry_point("supervisor")

workflow.add_conditional_edges(
    "supervisor",
    route_to_specialist,
    {
        "candidate_agent": "candidate_agent",
        "document_agent": "document_agent",
        "email_agent": "email_agent",
        "general_agent": "general_agent",
    },
)

workflow.add_edge("candidate_agent", END)
workflow.add_edge("document_agent", END)
workflow.add_edge("email_agent", END)
workflow.add_edge("general_agent", END)

chat_graph = workflow.compile()
