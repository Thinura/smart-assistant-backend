from fastapi.testclient import TestClient


def test_create_conversation(client: TestClient) -> None:
    response = client.post(
        "/api/v1/conversations",
        json={"title": "Test Conversation"},
    )

    assert response.status_code == 201
    data = response.json()

    assert data["title"] == "Test Conversation"
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


def test_list_conversations(client: TestClient) -> None:
    response = client.get("/api/v1/conversations")

    assert response.status_code == 200
    assert isinstance(response.json(), list)
