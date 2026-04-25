from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Smart Assistant Backend"
    environment: str = "local"
    api_v1_prefix: str = "/api/v1"

    database_url: str
    redis_url: str
    minio_endpoint: str
    ollama_base_url: str = "http://localhost:11434"
    default_llm_model: str = "llama3.1"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
