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
