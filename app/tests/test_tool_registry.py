from app.tools.registry import tool_registry


def test_tool_registry_lists_core_agent_tools(client) -> None:
    tools = tool_registry.list_tools()

    tool_names = {tool["name"] for tool in tools}

    assert "conversation_summary" in tool_names


def test_tool_registry_lists_db_tools(client, db_session) -> None:
    tools = tool_registry.list_tools(db=db_session)

    tool_names = {tool["name"] for tool in tools}

    assert "search_documents" in tool_names
    assert "review_candidate" in tool_names
    assert "create_approval_request" in tool_names
    assert "draft_candidate_email" in tool_names
    assert "match_candidate_to_job" in tool_names
    assert "generate_interview_kit" in tool_names
