from fastapi.testclient import TestClient


def test_chat_records_email_agent_in_agent_run_metadata(
    client: TestClient,
) -> None:
    template_response = client.post(
        "/api/v1/email-templates",
        json={
            "name": "Multi Agent Interview Invite",
            "template_type": "interview_invite",
            "subject_template": "Interview Invitation - {{ role_name }} at {{ company_name }}",
            "body_template": (
                "Hi {{ candidate_name }},\n\n"
                "Interview for {{ role_name }} at {{ company_name }}.\n\n"
                "Date: {{ interview_date }}\n"
                "Time: {{ interview_time }}\n"
                "Link: {{ interview_link }}\n\n"
                "{{ recruiter_name }}"
            ),
            "required_variables": [
                "candidate_name",
                "role_name",
                "company_name",
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
            "full_name": "Multi Agent Candidate",
            "email": "multi.agent@example.com",
            "role_applied_for": "QA Intern",
        },
    )

    assert candidate_response.status_code == 201

    conversation_response = client.post(
        "/api/v1/conversations",
        json={"title": "Multi-agent email test"},
    )

    assert conversation_response.status_code == 201

    candidate_id = candidate_response.json()["id"]

    chat_response = client.post(
        "/api/v1/chat",
        json={
            "conversation_id": conversation_response.json()["id"],
            "message": (
                f"Draft an interview invite email for candidate {candidate_id} "
                "on 10 May 2026 at 10:00 AM https://meet.google.com/test"
            ),
        },
    )

    assert chat_response.status_code == 201

    agent_run_id = chat_response.json()["agent_run_id"]

    agent_runs_response = client.get("/api/v1/agent-runs")

    assert agent_runs_response.status_code == 200

    matching_runs = [run for run in agent_runs_response.json() if run["id"] == agent_run_id]

    assert len(matching_runs) == 1

    run_metadata = matching_runs[0]["run_metadata"]

    assert run_metadata["mode"] == "multi_agent_langgraph"
    assert run_metadata["supervisor"] == "supervisor_agent"
    assert run_metadata["selected_agent"] == "email_agent"
    assert run_metadata["tool_results_count"] == 2
