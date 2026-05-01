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
    assert second_send_response.json()["detail"] == (
        "Only pending or failed outbox messages can be sent"
    )


def test_send_failed_outbox_message_can_be_retried(
    client: TestClient,
    monkeypatch,
) -> None:
    from app.services.email_providers.base import EmailSendResult
    from app.services.email_providers.console_provider import ConsoleEmailProvider

    call_count = {"count": 0}

    def fake_send(self, message):
        call_count["count"] += 1

        if call_count["count"] == 1:
            return EmailSendResult(
                success=False,
                error_message="Temporary SMTP failure",
            )

        return EmailSendResult(
            success=True,
            provider_message_id="retry-success-001",
        )

    monkeypatch.setattr(ConsoleEmailProvider, "send", fake_send)

    approval_response = client.post(
        "/api/v1/approvals",
        json={
            "action_type": "email_draft",
            "title": "Retry outbox test",
            "action_payload": {
                "candidate_email": "retry.test@example.com",
                "subject": "Retry test",
                "draft_body": "This is a retry test.",
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

    failed_data = first_send_response.json()

    assert failed_data["status"] == "failed"
    assert failed_data["error_message"] == "Temporary SMTP failure"

    retry_response = client.post(f"/api/v1/outbox/{outbox_message_id}/send")

    assert retry_response.status_code == 200

    retry_data = retry_response.json()

    assert retry_data["status"] == "sent"
    assert retry_data["provider_message_id"] == "retry-success-001"
    assert retry_data["error_message"] is None
    assert retry_data["sent_at"] is not None


def test_bulk_send_pending_outbox_messages(client: TestClient) -> None:
    outbox_ids = []

    for index in range(2):
        approval_response = client.post(
            "/api/v1/approvals",
            json={
                "action_type": "email_draft",
                "title": f"Bulk send test {index}",
                "action_payload": {
                    "candidate_email": f"bulk.send.{index}@example.com",
                    "subject": f"Bulk send test {index}",
                    "draft_body": f"This is bulk send test {index}.",
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

        outbox_ids.append(execute_response.json()["execution_result"]["outbox_message_id"])

    response = client.post(
        "/api/v1/outbox/send-pending",
        json={
            "limit": 10,
            "include_failed": False,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] >= 2
    assert data["sent_count"] >= 2

    returned_ids = {item["id"] for item in data["results"]}

    for outbox_id in outbox_ids:
        assert outbox_id in returned_ids

        detail_response = client.get(f"/api/v1/outbox/{outbox_id}")

        assert detail_response.status_code == 200
        assert detail_response.json()["status"] == "sent"


def test_outbox_summary_returns_counts(client: TestClient) -> None:
    approval_response = client.post(
        "/api/v1/approvals",
        json={
            "action_type": "email_draft",
            "title": "Outbox summary test",
            "action_payload": {
                "candidate_email": "summary.test@example.com",
                "subject": "Summary test",
                "draft_body": "This is a summary test.",
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

    summary_response = client.get("/api/v1/outbox/summary")

    assert summary_response.status_code == 200

    data = summary_response.json()

    assert data["pending_count"] >= 1
    assert data["total_count"] >= 1
    assert data["sent_count"] >= 0
    assert data["failed_count"] >= 0
