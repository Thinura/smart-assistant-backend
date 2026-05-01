from fastapi.testclient import TestClient


def test_create_approve_and_execute_approval_request(client: TestClient) -> None:
    create_response = client.post(
        "/api/v1/approvals",
        json={
            "action_type": "email_draft",
            "title": "Test approval",
            "description": "Testing approval lifecycle.",
            "action_payload": {
                "candidate_id": "test-candidate-id",
                "email_type": "rejection",
                "draft_body": "Testing approval.",
            },
        },
    )

    assert create_response.status_code == 201

    created = create_response.json()
    approval_id = created["id"]

    assert created["status"] == "pending"
    assert created["action_type"] == "email_draft"

    approve_response = client.post(
        f"/api/v1/approvals/{approval_id}/approve",
        json={
            "reviewed_by": "Thinura",
            "review_comment": "Approved in test.",
        },
    )

    assert approve_response.status_code == 200

    approved = approve_response.json()
    assert approved["status"] == "approved"
    assert approved["reviewed_by"] == "Thinura"

    execute_response = client.post(f"/api/v1/approvals/{approval_id}/execute")

    assert execute_response.status_code == 200

    executed = execute_response.json()

    assert executed["status"] == "executed"
    assert executed["execution_result"]["executed"] is True
    assert executed["execution_result"]["mode"] == "outbox"
    assert executed["execution_result"]["outbox_message_id"] is not None

    outbox_message_id = executed["execution_result"]["outbox_message_id"]

    outbox_response = client.get(f"/api/v1/outbox/{outbox_message_id}")

    assert outbox_response.status_code == 200

    outbox_data = outbox_response.json()

    assert outbox_data["approval_request_id"] == approval_id
    assert outbox_data["body"] == "Testing approval."
    assert outbox_data["status"] == "pending"


def test_reject_only_pending_approval_request(client: TestClient) -> None:
    create_response = client.post(
        "/api/v1/approvals",
        json={
            "action_type": "email_draft",
            "title": "Reject approval",
            "action_payload": {
                "candidate_id": "test-candidate-id",
                "email_type": "rejection",
                "draft_body": "Testing rejection.",
            },
        },
    )

    assert create_response.status_code == 201

    approval_id = create_response.json()["id"]

    reject_response = client.post(
        f"/api/v1/approvals/{approval_id}/reject",
        json={
            "reviewed_by": "Thinura",
            "review_comment": "Rejected in test.",
        },
    )

    assert reject_response.status_code == 200
    assert reject_response.json()["status"] == "rejected"

    approve_after_reject_response = client.post(
        f"/api/v1/approvals/{approval_id}/approve",
        json={
            "reviewed_by": "Thinura",
            "review_comment": "Should fail.",
        },
    )

    assert approve_after_reject_response.status_code == 400


def test_update_pending_approval_request(client: TestClient) -> None:
    create_response = client.post(
        "/api/v1/approvals",
        json={
            "action_type": "email_draft",
            "title": "Original approval title",
            "description": "Original description.",
            "action_payload": {
                "candidate_id": "test-candidate-id",
                "candidate_email": "candidate@example.com",
                "email_type": "interview_invite",
                "subject": "Original subject",
                "draft_body": "Original body.",
            },
        },
    )

    assert create_response.status_code == 201

    approval_id = create_response.json()["id"]

    update_response = client.patch(
        f"/api/v1/approvals/{approval_id}",
        json={
            "title": "Updated approval title",
            "description": "Updated description.",
            "action_payload": {
                "candidate_id": "test-candidate-id",
                "candidate_email": "candidate@example.com",
                "email_type": "interview_invite",
                "subject": "Updated subject",
                "draft_body": "Updated body with interview date and link.",
                "interview_date": "10 May 2026",
                "interview_time": "10:00 AM",
                "interview_link": "https://meet.google.com/test",
            },
        },
    )

    assert update_response.status_code == 200

    data = update_response.json()

    assert data["title"] == "Updated approval title"
    assert data["description"] == "Updated description."
    assert data["action_payload"]["subject"] == "Updated subject"
    assert data["action_payload"]["draft_body"] == ("Updated body with interview date and link.")
    assert data["action_payload"]["interview_date"] == "10 May 2026"


def test_update_approval_request_rejects_non_pending_request(
    client: TestClient,
) -> None:
    create_response = client.post(
        "/api/v1/approvals",
        json={
            "action_type": "email_draft",
            "title": "Approval update locked test",
            "action_payload": {
                "candidate_email": "locked@example.com",
                "subject": "Locked subject",
                "draft_body": "Locked body.",
            },
        },
    )

    assert create_response.status_code == 201

    approval_id = create_response.json()["id"]

    approve_response = client.post(
        f"/api/v1/approvals/{approval_id}/approve",
        json={
            "reviewed_by": "Thinura",
            "review_comment": "Approved.",
        },
    )

    assert approve_response.status_code == 200

    update_response = client.patch(
        f"/api/v1/approvals/{approval_id}",
        json={
            "title": "Should not update",
        },
    )

    assert update_response.status_code == 400
    assert update_response.json()["detail"] == ("Only pending approval requests can be updated")
