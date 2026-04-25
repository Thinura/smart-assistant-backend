from langgraph.graph import END, StateGraph

from app.agents.nodes import generate_assistant_response
from app.agents.state import AgentState


def build_chat_graph():
    graph = StateGraph(AgentState)

    graph.add_node("generate_assistant_response", generate_assistant_response)

    graph.set_entry_point("generate_assistant_response")
    graph.add_edge("generate_assistant_response", END)

    return graph.compile()


chat_graph = build_chat_graph()
