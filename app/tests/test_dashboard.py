from fastapi.testclient import TestClient


def test_get_dashboard_summary(client: TestClient) -> None:
    candidate_response = client.post(
        "/api/v1/candidates",
        json={
            "full_name": "Dashboard Candidate",
            "email": "dashboard.candidate@example.com",
            "role_applied_for": "QA Intern",
        },
    )

    assert candidate_response.status_code == 201

    approval_response = client.post(
        "/api/v1/approvals",
        json={
            "action_type": "email_draft",
            "title": "Dashboard approval",
            "action_payload": {
                "candidate_email": "dashboard.candidate@example.com",
                "subject": "Dashboard test",
                "draft_body": "Testing dashboard.",
            },
        },
    )

    assert approval_response.status_code == 201

    response = client.get("/api/v1/dashboard/summary")

    assert response.status_code == 200

    data = response.json()

    assert data["candidate_count"] >= 1
    assert data["approval_request_count"] >= 1
    assert data["pending_approval_count"] >= 1
    assert "document_count" in data
    assert "candidate_review_count" in data
    assert "outbox_message_count" in data
    assert "pending_outbox_count" in data
    assert "sent_outbox_count" in data
    assert "agent_run_count" in data
    assert "failed_agent_run_count" in data
