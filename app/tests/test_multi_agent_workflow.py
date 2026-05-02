from fastapi.testclient import TestClient

from app.tools.candidate_tools import ReviewCandidateTool


def test_multi_step_interview_workflow_creates_approval(
    client: TestClient,
    monkeypatch,
) -> None:
    class FakeStructuredReview:
        def model_dump(self) -> dict[str, object]:
            return {
                "summary": "Strong QA intern candidate.",
                "score": 86,
                "recommendation": "shortlist",
                "confidence": "high",
                "strengths": ["manual testing", "bug reporting"],
                "risks": [],
                "interview_focus_areas": ["test cases"],
            }

    def fake_generate_structured_review(self, candidate, cv_text):
        return FakeStructuredReview()

    monkeypatch.setattr(
        ReviewCandidateTool,
        "_generate_structured_review",
        fake_generate_structured_review,
    )

    template_response = client.post(
        "/api/v1/email-templates",
        json={
            "name": "Workflow Interview Invite",
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

    cv_response = client.post(
        "/api/v1/documents/upload",
        files={
            "file": (
                "workflow-cv.txt",
                b"QA intern with manual testing and bug reporting.",
                "text/plain",
            )
        },
        data={"document_type": "cv"},
    )
    assert cv_response.status_code == 201

    candidate_response = client.post(
        "/api/v1/candidates",
        json={
            "full_name": "Workflow Candidate",
            "email": "workflow.candidate@example.com",
            "role_applied_for": "QA Intern",
            "cv_document_id": cv_response.json()["id"],
        },
    )
    assert candidate_response.status_code == 201

    conversation_response = client.post(
        "/api/v1/conversations",
        json={"title": "Workflow agent test"},
    )
    assert conversation_response.status_code == 201

    candidate_id = candidate_response.json()["id"]

    chat_response = client.post(
        "/api/v1/chat",
        json={
            "conversation_id": conversation_response.json()["id"],
            "message": (
                f"Prepare interview workflow for candidate {candidate_id} "
                "on 10 May 2026 at 10:00 AM https://meet.google.com/test"
            ),
        },
    )

    assert chat_response.status_code == 201, chat_response.json()

    data = chat_response.json()

    assert "Interview workflow prepared successfully" in data["assistant_message"]
    assert "Approval Request ID:" in data["assistant_message"]

    agent_run_id = data["agent_run_id"]

    agent_runs_response = client.get("/api/v1/agent-runs")
    assert agent_runs_response.status_code == 200

    matching_runs = [run for run in agent_runs_response.json() if run["id"] == agent_run_id]

    assert len(matching_runs) == 1
    assert matching_runs[0]["run_metadata"]["selected_agent"] == "workflow_agent"


def test_multi_step_interview_workflow_with_job_description(
    client: TestClient,
    monkeypatch,
) -> None:
    class FakeStructuredReview:
        def model_dump(self) -> dict[str, object]:
            return {
                "summary": "Strong QA intern candidate.",
                "score": 88,
                "recommendation": "shortlist",
                "confidence": "high",
                "strengths": ["manual testing", "bug reporting"],
                "risks": [],
                "interview_focus_areas": ["test cases"],
            }

    def fake_generate_structured_review(self, candidate, cv_text):
        return FakeStructuredReview()

    monkeypatch.setattr(
        ReviewCandidateTool,
        "_generate_structured_review",
        fake_generate_structured_review,
    )

    template_response = client.post(
        "/api/v1/email-templates",
        json={
            "name": "Workflow JD Interview Invite",
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

    cv_response = client.post(
        "/api/v1/documents/upload",
        files={
            "file": (
                "workflow-jd-cv.txt",
                b"QA intern with manual testing, test cases, and bug reporting.",
                "text/plain",
            )
        },
        data={"document_type": "cv"},
    )
    assert cv_response.status_code == 201

    jd_response = client.post(
        "/api/v1/documents/upload",
        files={
            "file": (
                "workflow-qa-intern-jd.txt",
                b"QA Intern role requires manual testing, bug reporting, "
                b"test cases, and basic automation knowledge.",
                "text/plain",
            )
        },
        data={"document_type": "job_description"},
    )
    assert jd_response.status_code == 201

    candidate_response = client.post(
        "/api/v1/candidates",
        json={
            "full_name": "Workflow JD Candidate",
            "email": "workflow.jd@example.com",
            "role_applied_for": "QA Intern",
            "cv_document_id": cv_response.json()["id"],
        },
    )
    assert candidate_response.status_code == 201

    conversation_response = client.post(
        "/api/v1/conversations",
        json={"title": "Workflow agent JD test"},
    )
    assert conversation_response.status_code == 201

    candidate_id = candidate_response.json()["id"]
    jd_id = jd_response.json()["id"]

    chat_response = client.post(
        "/api/v1/chat",
        json={
            "conversation_id": conversation_response.json()["id"],
            "message": (
                f"Prepare interview workflow for candidate {candidate_id} "
                f"for QA Intern using job description {jd_id} "
                "on 10 May 2026 at 10:00 AM https://meet.google.com/test"
            ),
        },
    )

    assert chat_response.status_code == 201, chat_response.json()

    data = chat_response.json()

    assert "Interview workflow prepared successfully" in data["assistant_message"]
    assert "Review Score: 88/100" in data["assistant_message"]
    assert "Job match score:" in data["assistant_message"]
    assert "Interview kit created:" in data["assistant_message"]
    assert "Approval Request ID:" in data["assistant_message"]

    agent_run_id = data["agent_run_id"]

    agent_runs_response = client.get("/api/v1/agent-runs")
    assert agent_runs_response.status_code == 200

    matching_runs = [run for run in agent_runs_response.json() if run["id"] == agent_run_id]

    assert len(matching_runs) == 1

    run_metadata = matching_runs[0]["run_metadata"]

    assert run_metadata["selected_agent"] == "workflow_agent"
    assert run_metadata["tool_results_count"] == 5
