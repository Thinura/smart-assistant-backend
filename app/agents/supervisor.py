from app.agents.state import AgentState


def supervisor_agent(state: AgentState) -> AgentState:
    message = state["user_message"].lower()

    if any(
        phrase in message
        for phrase in [
            "prepare interview workflow",
            "run interview workflow",
            "candidate interview workflow",
            "full interview workflow",
        ]
    ):
        selected_agent = "workflow_agent"

    elif any(
        phrase in message
        for phrase in [
            "review candidate",
            "candidate review",
            "evaluate candidate",
            "screen candidate",
        ]
    ):
        selected_agent = "candidate_agent"

    elif any(
        phrase in message
        for phrase in [
            "draft email",
            "email",
            "invite",
            "rejection",
            "shortlist email",
            "interview invite",
        ]
    ):
        selected_agent = "email_agent"

    elif any(
        phrase in message
        for phrase in [
            "document",
            "policy",
            "uploaded",
            "search",
            "ask",
            "what does",
            "where does",
        ]
    ):
        selected_agent = "document_agent"

    else:
        selected_agent = "general_agent"

    return {
        **state,
        "selected_agent": selected_agent,
    }
