from fastapi.testclient import TestClient


def test_search_documents_returns_matching_chunks(client: TestClient) -> None:
    upload_response = client.post(
        "/api/v1/documents/upload",
        files={
            "file": (
                "policy-search.txt",
                b"Employees can work from home every Friday. "
                b"Office attendance is required Monday to Thursday.",
                "text/plain",
            )
        },
        data={"document_type": "policy"},
    )

    assert upload_response.status_code == 201

    response = client.post(
        "/api/v1/documents/search",
        json={
            "query": "When can employees work from home?",
            "document_type": "policy",
            "limit": 3,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["query"] == "When can employees work from home?"
    assert data["result_count"] >= 1
    assert data["results"][0]["document_type"] == "policy"
    assert "work from home" in data["results"][0]["content"].lower()
    assert data["results"][0]["similarity_score"] >= 0
