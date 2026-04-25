from langgraph.graph import END, StateGraph

from app.agents.nodes import classify_intent
from app.agents.registry import INTENT_NODE_REGISTRY
from app.agents.state import AgentState


def route_by_intent(state: AgentState) -> str:
    return state["intent"].value


def build_chat_graph():
    graph = StateGraph(AgentState)

    graph.add_node("classify_intent", classify_intent)

    for intent, node in INTENT_NODE_REGISTRY.items():
        graph.add_node(intent.value, node)

    graph.set_entry_point("classify_intent")

    graph.add_conditional_edges(
        "classify_intent",
        route_by_intent,
        {intent.value: intent.value for intent in INTENT_NODE_REGISTRY},
    )

    for intent in INTENT_NODE_REGISTRY:
        graph.add_edge(intent.value, END)

    return graph.compile()


chat_graph = build_chat_graph()
