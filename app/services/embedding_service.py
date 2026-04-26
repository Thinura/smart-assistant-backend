import httpx

from app.core.config import get_settings


class EmbeddingService:
    def __init__(self) -> None:
        self.settings = get_settings()

    def generate_embedding(self, text: str) -> list[float]:
        response = httpx.post(
            f"{self.settings.ollama_base_url}/api/embeddings",
            json={
                "model": self.settings.default_embedding_model,
                "prompt": text,
            },
            timeout=60,
        )
        response.raise_for_status()

        data = response.json()
        embedding = data.get("embedding")

        if not isinstance(embedding, list):
            raise RuntimeError("Embedding response did not contain a valid embedding list")

        return [float(value) for value in embedding]
