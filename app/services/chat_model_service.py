from langchain_ollama import ChatOllama

from app.core.config import get_settings


def get_chat_model() -> ChatOllama:
    settings = get_settings()

    return ChatOllama(
        model=settings.default_llm_model,
        base_url=settings.ollama_base_url,
        temperature=0.2,
    )
