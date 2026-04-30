from fastapi.testclient import TestClient


def test_execute_approved_email_creates_outbox_message(client: TestClient) -> None:
    approval_response = client.post(
        "/api/v1/approvals",
        json={
            "action_type": "email_draft",
            "title": "Approve outbox email",
            "description": "Testing outbox execution.",
            "action_payload": {
                "candidate_id": None,
                "candidate_email": "candidate@example.com",
                "email_type": "rejection",
                "subject": "Application update",
                "draft_body": "Thank you for applying.",
            },
        },
    )

    assert approval_response.status_code == 201

    approval_id = approval_response.json()["id"]

    approve_response = client.post(
        f"/api/v1/approvals/{approval_id}/approve",
        json={
            "reviewed_by": "Thinura",
            "review_comment": "Approved for outbox test.",
        },
    )

    assert approve_response.status_code == 200

    execute_response = client.post(f"/api/v1/approvals/{approval_id}/execute")

    assert execute_response.status_code == 200

    execution_result = execute_response.json()["execution_result"]

    assert execution_result["mode"] == "outbox"
    assert execution_result["executed"] is True
    assert execution_result["outbox_message_id"] is not None

    outbox_message_id = execution_result["outbox_message_id"]

    outbox_response = client.get(f"/api/v1/outbox/{outbox_message_id}")

    assert outbox_response.status_code == 200

    outbox_data = outbox_response.json()

    assert outbox_data["approval_request_id"] == approval_id
    assert outbox_data["recipient_email"] == "candidate@example.com"
    assert outbox_data["subject"] == "Application update"
    assert outbox_data["body"] == "Thank you for applying."
    assert outbox_data["status"] == "pending"


def test_list_outbox_messages_can_filter_by_status(client: TestClient) -> None:
    approval_response = client.post(
        "/api/v1/approvals",
        json={
            "action_type": "email_draft",
            "title": "Approve filtered outbox email",
            "action_payload": {
                "candidate_email": "filter@example.com",
                "subject": "Filter test",
                "draft_body": "Filter body.",
            },
        },
    )

    assert approval_response.status_code == 201

    approval_id = approval_response.json()["id"]

    approve_response = client.post(
        f"/api/v1/approvals/{approval_id}/approve",
        json={
            "reviewed_by": "Thinura",
            "review_comment": "Approved.",
        },
    )

    assert approve_response.status_code == 200

    execute_response = client.post(f"/api/v1/approvals/{approval_id}/execute")

    assert execute_response.status_code == 200

    response = client.get("/api/v1/outbox", params={"status": "pending"})

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["recipient_email"] == "filter@example.com"


def test_mark_outbox_message_sent(client: TestClient) -> None:
    approval_response = client.post(
        "/api/v1/approvals",
        json={
            "action_type": "email_draft",
            "title": "Approve mark sent email",
            "action_payload": {
                "candidate_email": "sent@example.com",
                "subject": "Sent test",
                "draft_body": "Sent body.",
            },
        },
    )

    assert approval_response.status_code == 201

    approval_id = approval_response.json()["id"]

    client.post(
        f"/api/v1/approvals/{approval_id}/approve",
        json={
            "reviewed_by": "Thinura",
            "review_comment": "Approved.",
        },
    )

    execute_response = client.post(f"/api/v1/approvals/{approval_id}/execute")

    outbox_message_id = execute_response.json()["execution_result"]["outbox_message_id"]

    response = client.post(
        f"/api/v1/outbox/{outbox_message_id}/mark-sent",
        json={
            "provider_message_id": "test-provider-123",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "sent"
    assert data["provider_message_id"] == "test-provider-123"
    assert data["sent_at"] is not None
