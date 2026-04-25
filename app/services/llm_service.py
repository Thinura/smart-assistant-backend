import httpx

from app.core.config import get_settings


class LLMService:
    def __init__(self) -> None:
        self.settings = get_settings()

    def generate_response(self, prompt: str) -> str:
        response = httpx.post(
            f"{self.settings.ollama_base_url}/api/generate",
            json={
                "model": self.settings.default_llm_model,
                "prompt": prompt,
                "stream": False,
            },
            timeout=60,
        )
        response.raise_for_status()

        data = response.json()
        return str(data.get("response", "")).strip()