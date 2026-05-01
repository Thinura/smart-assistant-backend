from fastapi.testclient import TestClient

from app.services import interview_kit_service


def test_generate_interview_kit_for_candidate(
    client: TestClient,
    monkeypatch,
) -> None:
    class FakeResponse:
        content = """
        {
          "summary": "Interview should focus on QA fundamentals and bug reporting.",
          "technical_questions": [
            {
              "question": "How do you write a good test case?",
              "purpose": "Assess test design basics.",
              "expected_signals": ["clear steps", "expected result", "edge cases"]
            }
          ],
          "behavioral_questions": [
            {
              "question": "Tell me about a time you found an important bug.",
              "purpose": "Assess ownership and communication.",
              "expected_signals": ["clear communication", "impact awareness"]
            }
          ],
          "risk_based_questions": [
            {
              "question": "How comfortable are you with automation testing?",
              "purpose": "Validate automation gap.",
              "expected_signals": ["honesty", "learning mindset"]
            }
          ],
          "evaluation_rubric": [
            {
              "area": "QA fundamentals",
              "strong_signal": "Explains test cases clearly with examples.",
              "weak_signal": "Only gives vague testing definitions."
            }
          ]
        }
        """

    class FakeModel:
        def invoke(self, messages):
            return FakeResponse()

    monkeypatch.setattr(
        interview_kit_service,
        "get_chat_model",
        lambda: FakeModel(),
    )

    cv_response = client.post(
        "/api/v1/documents/upload",
        files={
            "file": (
                "interview-kit-cv.txt",
                b"Candidate has manual testing and bug reporting experience.",
                "text/plain",
            )
        },
        data={"document_type": "cv"},
    )

    assert cv_response.status_code == 201

    candidate_response = client.post(
        "/api/v1/candidates",
        json={
            "full_name": "Interview Kit Candidate",
            "email": "interview.kit@example.com",
            "role_applied_for": "QA Intern",
            "cv_document_id": cv_response.json()["id"],
        },
    )

    assert candidate_response.status_code == 201

    candidate_id = candidate_response.json()["id"]

    response = client.post(
        f"/api/v1/candidates/{candidate_id}/interview-kit",
        json={
            "role_name": "QA Intern",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["candidate_id"] == candidate_id
    assert data["summary"]
    assert len(data["technical_questions"]) == 1
    assert len(data["behavioral_questions"]) == 1
    assert len(data["risk_based_questions"]) == 1
    assert len(data["evaluation_rubric"]) == 1

    list_response = client.get(f"/api/v1/candidates/{candidate_id}/interview-kits")

    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    get_response = client.get(f"/api/v1/interview-kits/{data['id']}")

    assert get_response.status_code == 200
    assert get_response.json()["id"] == data["id"]
