from fastapi.testclient import TestClient

from app.services import document_qa_service


def test_ask_document_question_returns_answer_with_sources(
    client: TestClient,
    monkeypatch,
) -> None:
    class FakeResponse:
        content = "Employees can work from home every Friday."

    class FakeModel:
        def invoke(self, messages):
            return FakeResponse()

    monkeypatch.setattr(
        document_qa_service,
        "get_chat_model",
        lambda: FakeModel(),
    )

    upload_response = client.post(
        "/api/v1/documents/upload",
        files={
            "file": (
                "qa-policy.txt",
                b"Employees can work from home every Friday. "
                b"Office attendance is required Monday to Thursday.",
                "text/plain",
            )
        },
        data={"document_type": "policy"},
    )

    assert upload_response.status_code == 201

    response = client.post(
        "/api/v1/documents/ask",
        json={
            "question": "When can employees work from home?",
            "document_type": "policy",
            "limit": 3,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["question"] == "When can employees work from home?"
    assert data["answer"] == "Employees can work from home every Friday."
    assert data["source_count"] >= 1
    assert len(data["sources"]) >= 1
    assert "work from home" in data["sources"][0]["content"].lower()
