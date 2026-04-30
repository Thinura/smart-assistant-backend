from fastapi.testclient import TestClient

from app.tools.candidate_tools import ReviewCandidateTool


def test_review_candidate_persists_candidate_review(
    client: TestClient,
    monkeypatch,
) -> None:
    class FakeStructuredReview:
        def model_dump(self) -> dict:
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
