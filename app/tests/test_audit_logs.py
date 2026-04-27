from fastapi.testclient import TestClient


def test_audit_logs_can_filter_by_event_type(client: TestClient) -> None:
    create_response = client.post(
        "/api/v1/approvals",
        json={
            "action_type": "email_draft",
            "title": "Audit filter test",
            "action_payload": {
                "candidate_id": "test-candidate-id",
                "email_type": "rejection",
                "draft_body": "Testing audit filtering.",
            },
        },
    )

    assert create_response.status_code == 201

    response = client.get(
        "/api/v1/audit-logs",
        params={
            "event_type": "approval.created",
            "limit": 10,
        },
    )

    assert response.status_code == 200

    logs = response.json()

    assert len(logs) > 0
    assert all(log["event_type"] == "approval.created" for log in logs)


def test_audit_logs_can_filter_by_actor(client: TestClient) -> None:
    create_response = client.post(
        "/api/v1/approvals",
        json={
            "action_type": "email_draft",
            "title": "Audit actor test",
            "action_payload": {
                "candidate_id": "test-candidate-id",
                "email_type": "rejection",
                "draft_body": "Testing audit actor filtering.",
            },
        },
    )

    assert create_response.status_code == 201

    approval_id = create_response.json()["id"]

    approve_response = client.post(
        f"/api/v1/approvals/{approval_id}/approve",
        json={
            "reviewed_by": "Thinura",
            "review_comment": "Testing actor filter.",
        },
    )

    assert approve_response.status_code == 200

    response = client.get(
        "/api/v1/audit-logs",
        params={
            "actor": "Thinura",
            "limit": 10,
        },
    )

    assert response.status_code == 200

    logs = response.json()

    assert len(logs) > 0
    assert all(log["actor"] == "Thinura" for log in logs)
