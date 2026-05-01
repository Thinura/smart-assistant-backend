from fastapi.testclient import TestClient


def test_send_outbox_message_with_console_provider(client: TestClient) -> None:
    approval_response = client.post(
        "/api/v1/approvals",
        json={
            "action_type": "email_draft",
            "title": "Send outbox test",
            "action_payload": {
                "candidate_email": "send.test@example.com",
                "subject": "Send test",
                "draft_body": "This is a send test.",
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

    outbox_message_id = execute_response.json()["execution_result"]["outbox_message_id"]

    send_response = client.post(f"/api/v1/outbox/{outbox_message_id}/send")

    assert send_response.status_code == 200

    data = send_response.json()

    assert data["status"] == "sent"
    assert data["provider_message_id"].startswith("console-")
    assert data["sent_at"] is not None


def test_send_outbox_message_rejects_non_pending_message(client: TestClient) -> None:
    approval_response = client.post(
        "/api/v1/approvals",
        json={
            "action_type": "email_draft",
            "title": "Send twice test",
            "action_payload": {
                "candidate_email": "send.twice@example.com",
                "subject": "Send twice test",
                "draft_body": "This is a send twice test.",
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

    outbox_message_id = execute_response.json()["execution_result"]["outbox_message_id"]

    first_send_response = client.post(f"/api/v1/outbox/{outbox_message_id}/send")

    assert first_send_response.status_code == 200

    second_send_response = client.post(f"/api/v1/outbox/{outbox_message_id}/send")

    assert second_send_response.status_code == 400
    assert second_send_response.json()["detail"] == "Only pending outbox messages can be sent"
