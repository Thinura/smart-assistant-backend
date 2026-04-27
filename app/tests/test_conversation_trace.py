from fastapi.testclient import TestClient


def test_conversation_trace_returns_summary_only_when_sections_disabled(client: TestClient) -> None:
    create_response = client.post(
        "/api/v1/conversations",
        json={
            "title": "Trace test conversation",
        },
    )

    assert create_response.status_code == 201

    conversation_id = create_response.json()["id"]

    response = client.get(
        f"/api/v1/conversations/{conversation_id}/trace",
        params={
            "include_messages": False,
            "include_agent_runs": False,
            "include_tool_calls": False,
            "include_approvals": False,
            "include_audit_logs": False,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["summary"]["conversation_id"] == conversation_id
    assert data["summary"]["message_count"] == 0
    assert data["summary"]["agent_run_count"] == 0
    assert data["summary"]["tool_call_count"] == 0
    assert data["summary"]["approval_request_count"] == 0
    assert data["summary"]["pending_approval_count"] == 0
    assert data["summary"]["has_failed_run"] is False

    assert data["messages"] == []
    assert data["agent_runs"] == []
    assert data["tool_calls"] == []
    assert data["approval_requests"] == []
    assert data["audit_logs"] == []


def test_conversation_trace_returns_404_for_missing_conversation(client: TestClient) -> None:
    response = client.get("/api/v1/conversations/00000000-0000-0000-0000-000000000000/trace")

    assert response.status_code == 404
