from fastapi.testclient import TestClient

from app.tools.candidate_tools import ReviewCandidateTool


def test_shortlisted_candidate_review_creates_interview_approval(
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
                "strengths": ["manual testing", "test cases"],
                "risks": [],
                "interview_focus_areas": ["bug reporting"],
            }

    def fake_generate_structured_review(self, candidate, cv_text):
        return FakeStructuredReview()

    monkeypatch.setattr(
        ReviewCandidateTool,
        "_generate_structured_review",
        fake_generate_structured_review,
    )

    cv_response = client.post(
        "/api/v1/documents/upload",
        files={
            "file": (
                "automation-cv.txt",
                b"QA candidate with manual testing and bug reporting.",
                "text/plain",
            )
        },
        data={"document_type": "cv"},
    )

    assert cv_response.status_code == 201

    candidate_response = client.post(
        "/api/v1/candidates",
        json={
            "full_name": "Automation Candidate",
            "email": "automation.candidate@example.com",
            "role_applied_for": "QA Intern",
            "cv_document_id": cv_response.json()["id"],
        },
    )

    assert candidate_response.status_code == 201

    candidate_id = candidate_response.json()["id"]

    tool_response = client.post(
        "/api/v1/tools/review_candidate/run",
        json={
            "payload": {
                "candidate_id": candidate_id,
                "role": "QA Intern",
            },
        },
    )

    assert tool_response.status_code == 200
    assert tool_response.json()["success"] is True

    approvals_response = client.get("/api/v1/approvals")

    assert approvals_response.status_code == 200

    approvals = approvals_response.json()

    matching_approvals = [
        approval
        for approval in approvals
        if approval["action_payload"].get("candidate_id") == candidate_id
        and approval["action_payload"].get("email_type") == "interview_invite"
    ]

    assert len(matching_approvals) == 1

    approval = matching_approvals[0]

    assert approval["status"] == "pending"
    assert approval["action_type"] == "email_draft"
    assert approval["action_payload"]["candidate_email"] == ("automation.candidate@example.com")
    assert approval["action_payload"]["source"] == "candidate_pipeline_automation"


def test_shortlisted_candidate_review_does_not_duplicate_interview_approval(
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
                "strengths": ["manual testing"],
                "risks": [],
                "interview_focus_areas": ["bug reporting"],
            }

    def fake_generate_structured_review(self, candidate, cv_text):
        return FakeStructuredReview()

    monkeypatch.setattr(
        ReviewCandidateTool,
        "_generate_structured_review",
        fake_generate_structured_review,
    )

    cv_response = client.post(
        "/api/v1/documents/upload",
        files={
            "file": (
                "automation-duplicate-cv.txt",
                b"QA candidate with manual testing.",
                "text/plain",
            )
        },
        data={"document_type": "cv"},
    )

    assert cv_response.status_code == 201

    candidate_response = client.post(
        "/api/v1/candidates",
        json={
            "full_name": "Automation Duplicate Candidate",
            "email": "automation.duplicate@example.com",
            "role_applied_for": "QA Intern",
            "cv_document_id": cv_response.json()["id"],
        },
    )

    assert candidate_response.status_code == 201

    candidate_id = candidate_response.json()["id"]

    for _ in range(2):
        tool_response = client.post(
            "/api/v1/tools/review_candidate/run",
            json={
                "payload": {
                    "candidate_id": candidate_id,
                    "role": "QA Intern",
                },
            },
        )

        assert tool_response.status_code == 200
        assert tool_response.json()["success"] is True

    approvals_response = client.get("/api/v1/approvals")

    assert approvals_response.status_code == 200

    approvals = approvals_response.json()

    matching_approvals = [
        approval
        for approval in approvals
        if approval["action_payload"].get("candidate_id") == candidate_id
        and approval["action_payload"].get("email_type") == "interview_invite"
        and approval["action_payload"]["source"] == "candidate_pipeline_automation"
        and approval["action_payload"].get("candidate_review_id") is not None
        and approval["action_payload"]["email_type"] == "interview_invite"
    ]

    assert len(matching_approvals) == 1
