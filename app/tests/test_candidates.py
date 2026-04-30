from fastapi.testclient import TestClient


def test_list_candidates_can_filter_by_status(client: TestClient) -> None:
    new_response = client.post(
        "/api/v1/candidates",
        json={
            "full_name": "New Candidate",
            "email": "new.candidate@example.com",
            "role_applied_for": "QA Intern",
        },
    )

    shortlisted_response = client.post(
        "/api/v1/candidates",
        json={
            "full_name": "Shortlisted Candidate",
            "email": "shortlisted.candidate@example.com",
            "role_applied_for": "QA Intern",
        },
    )

    assert new_response.status_code == 201
    assert shortlisted_response.status_code == 201

    shortlisted_id = shortlisted_response.json()["id"]

    update_response = client.patch(
        f"/api/v1/candidates/{shortlisted_id}",
        json={
            "status": "shortlisted",
        },
    )

    assert update_response.status_code == 200
    assert update_response.json()["status"] == "shortlisted"

    response = client.get("/api/v1/candidates", params={"status": "new"})

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["email"] == "new.candidate@example.com"


def test_list_candidates_can_filter_by_role(client: TestClient) -> None:
    qa_response = client.post(
        "/api/v1/candidates",
        json={
            "full_name": "QA Candidate",
            "email": "qa.candidate@example.com",
            "role_applied_for": "QA Intern",
        },
    )

    se_response = client.post(
        "/api/v1/candidates",
        json={
            "full_name": "SE Candidate",
            "email": "se.candidate@example.com",
            "role_applied_for": "Software Engineer Intern",
        },
    )

    assert qa_response.status_code == 201
    assert se_response.status_code == 201

    response = client.get("/api/v1/candidates", params={"role": "QA"})

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["email"] == "qa.candidate@example.com"


def test_list_candidates_can_search_by_name_or_email(client: TestClient) -> None:
    create_response = client.post(
        "/api/v1/candidates",
        json={
            "full_name": "Nathasha Perera",
            "email": "nathasha.perera@example.com",
            "role_applied_for": "QA Intern",
        },
    )

    other_response = client.post(
        "/api/v1/candidates",
        json={
            "full_name": "Other Candidate",
            "email": "other@example.com",
            "role_applied_for": "QA Intern",
        },
    )

    assert create_response.status_code == 201
    assert other_response.status_code == 201

    response = client.get("/api/v1/candidates", params={"search": "Nathasha"})

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["email"] == "nathasha.perera@example.com"


def test_get_candidate_by_id(client: TestClient) -> None:
    create_response = client.post(
        "/api/v1/candidates",
        json={
            "full_name": "Detail Candidate",
            "email": "detail.candidate@example.com",
            "role_applied_for": "QA Intern",
        },
    )

    assert create_response.status_code == 201

    candidate_id = create_response.json()["id"]

    response = client.get(f"/api/v1/candidates/{candidate_id}")

    assert response.status_code == 200
    assert response.json()["id"] == candidate_id


def test_get_candidate_returns_404_for_missing_candidate(client: TestClient) -> None:
    response = client.get("/api/v1/candidates/00000000-0000-0000-0000-000000000000")

    assert response.status_code == 404


def test_get_candidate_timeline(client: TestClient) -> None:
    create_response = client.post(
        "/api/v1/candidates",
        json={
            "full_name": "Timeline Candidate",
            "email": "timeline.candidate@example.com",
            "role_applied_for": "QA Intern",
        },
    )

    assert create_response.status_code == 201

    candidate_id = create_response.json()["id"]

    status_response = client.post(
        f"/api/v1/candidates/{candidate_id}/status",
        json={
            "status": "shortlisted",
            "reason": "Timeline test status change.",
            "updated_by": "Thinura",
        },
    )

    assert status_response.status_code == 200

    response = client.get(f"/api/v1/candidates/{candidate_id}/timeline")

    assert response.status_code == 200

    data = response.json()

    assert data["summary"]["candidate_id"] == candidate_id
    assert data["summary"]["has_cv"] is False
    assert data["summary"]["audit_log_count"] >= 2
    assert data["candidate"]["id"] == candidate_id
    assert data["cv_document"] is None

    event_types = [log["event_type"] for log in data["audit_logs"]]

    assert "candidate.created" in event_types
    assert "candidate.updated" in event_types


def test_get_candidate_timeline_returns_404_for_missing_candidate(
    client: TestClient,
) -> None:
    response = client.get("/api/v1/candidates/00000000-0000-0000-0000-000000000000/timeline")

    assert response.status_code == 404


def test_candidate_timeline_includes_outbox_messages(client: TestClient) -> None:
    candidate_response = client.post(
        "/api/v1/candidates",
        json={
            "full_name": "Outbox Timeline Candidate",
            "email": "outbox.timeline@example.com",
            "role_applied_for": "QA Intern",
        },
    )

    assert candidate_response.status_code == 201

    candidate = candidate_response.json()
    candidate_id = candidate["id"]

    approval_response = client.post(
        "/api/v1/approvals",
        json={
            "action_type": "email_draft",
            "title": "Approve timeline outbox email",
            "description": "Testing candidate timeline outbox integration.",
            "action_payload": {
                "candidate_id": candidate_id,
                "candidate_email": candidate["email"],
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
            "review_comment": "Approved for timeline test.",
        },
    )

    assert approve_response.status_code == 200

    execute_response = client.post(f"/api/v1/approvals/{approval_id}/execute")

    assert execute_response.status_code == 200

    timeline_response = client.get(f"/api/v1/candidates/{candidate_id}/timeline")

    assert timeline_response.status_code == 200

    data = timeline_response.json()

    assert data["summary"]["candidate_id"] == candidate_id
    assert data["summary"]["outbox_message_count"] == 1
    assert data["summary"]["sent_outbox_message_count"] == 0

    assert len(data["outbox_messages"]) == 1
    assert data["outbox_messages"][0]["recipient_email"] == candidate["email"]
    assert data["outbox_messages"][0]["subject"] == "Application update"
    assert data["outbox_messages"][0]["status"] == "pending"
