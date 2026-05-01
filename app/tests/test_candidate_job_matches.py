from fastapi.testclient import TestClient

from app.services import candidate_job_match_service


def test_match_candidate_to_job_persists_match(
    client: TestClient,
    monkeypatch,
) -> None:
    class FakeResponse:
        content = """
        {
          "summary": "The candidate is a good match for the QA Intern role.",
          "match_score": 84,
          "matched_skills": ["manual testing", "bug reporting"],
          "missing_skills": ["advanced automation"],
          "risks": ["limited Selenium experience"],
          "interview_focus_areas": ["automation basics"],
          "recommendation": "match",
          "confidence": "high"
        }
        """

    class FakeModel:
        def invoke(self, messages):
            return FakeResponse()

    monkeypatch.setattr(
        candidate_job_match_service,
        "get_chat_model",
        lambda: FakeModel(),
    )

    cv_response = client.post(
        "/api/v1/documents/upload",
        files={
            "file": (
                "match-cv.txt",
                b"Candidate has manual testing and bug reporting experience.",
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
                "match-jd.txt",
                b"QA Intern role requires manual testing, bug reporting, and basic automation.",
                "text/plain",
            )
        },
        data={"document_type": "job_description"},
    )

    assert jd_response.status_code == 201

    candidate_response = client.post(
        "/api/v1/candidates",
        json={
            "full_name": "Match Candidate",
            "email": "match.candidate@example.com",
            "role_applied_for": "QA Intern",
            "cv_document_id": cv_response.json()["id"],
        },
    )

    assert candidate_response.status_code == 201

    candidate_id = candidate_response.json()["id"]

    match_response = client.post(
        f"/api/v1/candidates/{candidate_id}/match-job",
        json={
            "job_description_document_id": jd_response.json()["id"],
            "role_name": "QA Intern",
        },
    )

    assert match_response.status_code == 201

    match_data = match_response.json()

    assert match_data["candidate_id"] == candidate_id
    assert match_data["match_score"] == 84
    assert match_data["recommendation"] == "match"
    assert match_data["confidence"] == "high"
    assert "manual testing" in match_data["matched_skills"]

    list_response = client.get(f"/api/v1/candidates/{candidate_id}/job-matches")

    assert list_response.status_code == 200

    matches = list_response.json()

    assert len(matches) == 1
    assert matches[0]["id"] == match_data["id"]
