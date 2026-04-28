from fastapi.testclient import TestClient


def test_list_approvals_can_filter_by_status(client: TestClient) -> None:
    pending_response = client.post(
        "/api/v1/approvals",
        json={
            "action_type": "email_draft",
            "title": "Pending approval",
            "action_payload": {"draft_body": "Pending"},
        },
    )

    approved_response = client.post(
        "/api/v1/approvals",
        json={
            "action_type": "email_draft",
            "title": "Approved approval",
            "action_payload": {"draft_body": "Approved"},
        },
    )

    assert pending_response.status_code == 201
    assert approved_response.status_code == 201

    approved_id = approved_response.json()["id"]

    approve_response = client.post(
        f"/api/v1/approvals/{approved_id}/approve",
        json={
            "reviewed_by": "Thinura",
            "review_comment": "Approved.",
        },
    )

    assert approve_response.status_code == 200

    response = client.get("/api/v1/approvals", params={"status": "pending"})

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["id"] == pending_response.json()["id"]
    assert data[0]["status"] == "pending"


def test_get_approval_request_by_id(client: TestClient) -> None:
    create_response = client.post(
        "/api/v1/approvals",
        json={
            "action_type": "email_draft",
            "title": "Get approval",
            "action_payload": {"draft_body": "Testing get."},
        },
    )

    assert create_response.status_code == 201

    approval_id = create_response.json()["id"]

    response = client.get(f"/api/v1/approvals/{approval_id}")

    assert response.status_code == 200
    assert response.json()["id"] == approval_id


def test_update_pending_approval_request(client: TestClient) -> None:
    create_response = client.post(
        "/api/v1/approvals",
        json={
            "action_type": "email_draft",
            "title": "Before update",
            "action_payload": {
                "draft_body": "Before",
            },
        },
    )

    assert create_response.status_code == 201

    approval_id = create_response.json()["id"]

    update_response = client.patch(
        f"/api/v1/approvals/{approval_id}",
        json={
            "title": "After update",
            "action_payload": {
                "draft_body": "After",
            },
        },
    )

    assert update_response.status_code == 200

    data = update_response.json()

    assert data["title"] == "After update"
    assert data["action_payload"]["draft_body"] == "After"


def test_cannot_update_approved_approval_request(client: TestClient) -> None:
    create_response = client.post(
        "/api/v1/approvals",
        json={
            "action_type": "email_draft",
            "title": "Cannot update after approval",
            "action_payload": {
                "draft_body": "Before",
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
            "title": "Should fail",
        },
    )

    assert update_response.status_code == 400
