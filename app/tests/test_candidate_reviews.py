from fastapi.testclient import TestClient

from app.tools.candidate_tools import ReviewCandidateTool


def test_review_candidate_persists_candidate_review(
    client: TestClient,
    monkeypatch,
) -> None:
    class FakeStructuredReview:
        def model_dump(self) -> dict[str, object]:
            return {
                "summary": "QA intern with manual testing, test cases, and bug reporting.",
                "score": 82,
                "recommendation": "shortlist",
                "confidence": "high",
                "strengths": ["manual testing", "test cases", "bug reporting"],
                "risks": ["limited automation exposure"],
                "interview_focus_areas": ["manual testing fundamentals"],
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
                "review-cv.txt",
                b"QA intern with manual testing, test cases, and bug reporting.",
                "text/plain",
            )
        },
        data={"document_type": "cv"},
    )

    assert cv_response.status_code == 201

    candidate_response = client.post(
        "/api/v1/candidates",
        json={
            "full_name": "Review Candidate",
            "email": "review.candidate@example.com",
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

    tool_data = tool_response.json()

    assert tool_data["success"] is True
    assert tool_data["data"]["candidate_review_id"] is not None

    review_id = tool_data["data"]["candidate_review_id"]

    review_response = client.get(f"/api/v1/candidate-reviews/{review_id}")

    assert review_response.status_code == 200

    review_data = review_response.json()

    assert review_data["candidate_id"] == candidate_id
    assert review_data["role_applied_for"] == "QA Intern"
    assert review_data["summary"]
    assert review_data["score"] == 82
    assert review_data["recommendation"] == "shortlist"
    assert review_data["confidence"] == "high"

    list_response = client.get(f"/api/v1/candidates/{candidate_id}/reviews")

    assert list_response.status_code == 200

    reviews = list_response.json()

    assert len(reviews) == 1
    assert reviews[0]["id"] == review_id


def test_review_candidate_persists_agent_run_id_when_payload_contains_it(
    client: TestClient,
    monkeypatch,
) -> None:
    class FakeStructuredReview:
        def model_dump(self) -> dict[str, object]:
            return {
                "summary": "Agent-linked review summary.",
                "score": 83,
                "recommendation": "shortlist",
                "confidence": "high",
                "strengths": ["manual testing"],
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

    conversation_response = client.post(
        "/api/v1/conversations",
        json={"title": "Agent review link test"},
    )
    assert conversation_response.status_code == 201

    chat_response = client.post(
        "/api/v1/chat",
        json={
            "conversation_id": conversation_response.json()["id"],
            "message": "Hello agent",
        },
    )
    assert chat_response.status_code == 201

    agent_runs_response = client.get("/api/v1/agent-runs")
    assert agent_runs_response.status_code == 200
    agent_run_id = agent_runs_response.json()[0]["id"]

    cv_response = client.post(
        "/api/v1/documents/upload",
        files={
            "file": (
                "agent-linked-review-cv.txt",
                b"QA intern with manual testing and test cases.",
                "text/plain",
            )
        },
        data={"document_type": "cv"},
    )
    assert cv_response.status_code == 201

    candidate_response = client.post(
        "/api/v1/candidates",
        json={
            "full_name": "Agent Linked Review Candidate",
            "email": "agent.linked.review@example.com",
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
                "agent_run_id": agent_run_id,
            },
        },
    )

    assert tool_response.status_code == 200
    assert tool_response.json()["success"] is True

    review_id = tool_response.json()["data"]["candidate_review_id"]

    review_response = client.get(f"/api/v1/candidate-reviews/{review_id}")

    assert review_response.status_code == 200
    assert review_response.json()["agent_run_id"] == agent_run_id
