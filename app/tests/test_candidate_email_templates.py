from fastapi.testclient import TestClient


def test_draft_candidate_email_uses_active_template(client: TestClient) -> None:
    template_response = client.post(
        "/api/v1/email-templates",
        json={
            "name": "Interview Invite Template",
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

    assert template_response.status_code == 201

    candidate_response = client.post(
        "/api/v1/candidates",
        json={
            "full_name": "Template Candidate",
            "email": "template.candidate@example.com",
            "role_applied_for": "QA Intern",
        },
    )

    assert candidate_response.status_code == 201

    candidate_id = candidate_response.json()["id"]

    tool_response = client.post(
        "/api/v1/tools/draft_candidate_email/run",
        json={
            "payload": {
                "candidate_id": candidate_id,
                "email_type": "interview_invite",
                "company_name": "Expernetic",
                "recruiter_name": "Thinura",
                "interview_date": "10 May 2026",
                "interview_time": "10:00 AM",
                "interview_link": "https://meet.google.com/test",
            },
        },
    )

    assert tool_response.status_code == 200

    data = tool_response.json()

    assert data["success"] is True
    assert data["data"]["email"]["subject"] == ("Interview Invitation - QA Intern at Expernetic")
    assert "Hi Template Candidate" in data["data"]["email"]["body"]
    assert "10 May 2026" in data["data"]["email"]["body"]
    assert "https://meet.google.com/test" in data["data"]["email"]["body"]
    assert data["data"]["email"]["template_id"] == template_response.json()["id"]


def test_draft_candidate_email_fails_when_template_variables_are_missing(
    client: TestClient,
) -> None:
    template_response = client.post(
        "/api/v1/email-templates",
        json={
            "name": "Interview Invite Missing Variable Template",
            "template_type": "interview_invite",
            "subject_template": "Interview Invitation - {{ role_name }}",
            "body_template": "Hi {{ candidate_name }}, Date: {{ interview_date }}",
            "required_variables": [
                "candidate_name",
                "role_name",
                "interview_date",
            ],
            "optional_variables": [],
            "is_active": True,
        },
    )

    assert template_response.status_code == 201

    candidate_response = client.post(
        "/api/v1/candidates",
        json={
            "full_name": "Missing Variable Candidate",
            "email": "missing.variable@example.com",
            "role_applied_for": "QA Intern",
        },
    )

    assert candidate_response.status_code == 201

    tool_response = client.post(
        "/api/v1/tools/draft_candidate_email/run",
        json={
            "payload": {
                "candidate_id": candidate_response.json()["id"],
                "email_type": "interview_invite",
            },
        },
    )

    assert tool_response.status_code == 200

    data = tool_response.json()

    assert data["success"] is False
    assert "interview_date" in data["error"]
