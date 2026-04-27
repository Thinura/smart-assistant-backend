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
    assert executed["execution_result"]["mode"] == "dry_run"


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
