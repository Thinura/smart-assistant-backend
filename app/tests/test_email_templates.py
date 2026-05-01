from fastapi.testclient import TestClient


def test_create_and_render_email_template(client: TestClient) -> None:
    create_response = client.post(
        "/api/v1/email-templates",
        json={
            "name": "QA Intern Interview Invite",
            "template_type": "interview_invite",
            "subject_template": "Interview Invitation - {{ role_name }} at {{ company_name }}",
            "body_template": (
                "Hi {{ candidate_name }},\n\n"
                "We are pleased to invite you for an interview for the "
                "{{ role_name }} position at {{ company_name }}.\n\n"
                "Date: {{ interview_date }}\n"
                "Time: {{ interview_time }}\n"
                "Interview Link: {{ interview_link }}\n\n"
                "Best regards,\n"
                "{{ recruiter_name }}"
            ),
            "required_variables": [
                "candidate_name",
                "company_name",
                "role_name",
                "interview_date",
                "interview_time",
                "interview_link",
                "recruiter_name",
            ],
            "optional_variables": [],
            "is_active": True,
        },
    )

    assert create_response.status_code == 201

    template_id = create_response.json()["id"]

    render_response = client.post(
        f"/api/v1/email-templates/{template_id}/render",
        json={
            "variables": {
                "candidate_name": "Nimal Perera",
                "company_name": "Expernetic",
                "role_name": "QA Intern",
                "interview_date": "10 May 2026",
                "interview_time": "10:00 AM",
                "interview_link": "https://meet.google.com/test",
                "recruiter_name": "Thinura",
            }
        },
    )

    assert render_response.status_code == 200

    data = render_response.json()

    assert data["subject"] == "Interview Invitation - QA Intern at Expernetic"
    assert "Hi Nimal Perera" in data["body"]
    assert "10 May 2026" in data["body"]
    assert "https://meet.google.com/test" in data["body"]
    assert data["missing_variables"] == []


def test_render_email_template_returns_422_for_missing_variables(
    client: TestClient,
) -> None:
    create_response = client.post(
        "/api/v1/email-templates",
        json={
            "name": "Missing Variables Template",
            "template_type": "interview_invite",
            "subject_template": "Interview - {{ role_name }}",
            "body_template": "Hi {{ candidate_name }}, date: {{ interview_date }}",
            "required_variables": [
                "candidate_name",
                "role_name",
                "interview_date",
            ],
            "optional_variables": [],
            "is_active": True,
        },
    )

    assert create_response.status_code == 201

    template_id = create_response.json()["id"]

    render_response = client.post(
        f"/api/v1/email-templates/{template_id}/render",
        json={
            "variables": {
                "candidate_name": "Nimal Perera",
                "role_name": "QA Intern",
            }
        },
    )

    assert render_response.status_code == 422
    assert "interview_date" in render_response.json()["detail"]


def test_list_email_templates_can_filter_by_type(client: TestClient) -> None:
    create_response = client.post(
        "/api/v1/email-templates",
        json={
            "name": "Rejection Template",
            "template_type": "rejection",
            "subject_template": "Application update - {{ role_name }}",
            "body_template": "Hi {{ candidate_name }}, thank you for applying.",
            "required_variables": ["candidate_name", "role_name"],
            "optional_variables": [],
            "is_active": True,
        },
    )

    assert create_response.status_code == 201

    response = client.get(
        "/api/v1/email-templates",
        params={"template_type": "rejection"},
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) >= 1
    assert data[0]["template_type"] == "rejection"


def test_update_email_template(client: TestClient) -> None:
    create_response = client.post(
        "/api/v1/email-templates",
        json={
            "name": "General Template",
            "template_type": "general",
            "subject_template": "Hello {{ candidate_name }}",
            "body_template": "Hi {{ candidate_name }}",
            "required_variables": ["candidate_name"],
            "optional_variables": [],
            "is_active": True,
        },
    )

    assert create_response.status_code == 201

    template_id = create_response.json()["id"]

    update_response = client.patch(
        f"/api/v1/email-templates/{template_id}",
        json={
            "name": "Updated General Template",
            "is_active": False,
        },
    )

    assert update_response.status_code == 200

    data = update_response.json()

    assert data["name"] == "Updated General Template"
    assert data["is_active"] is False
