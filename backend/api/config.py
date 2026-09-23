"""Application configuration using Pydantic Settings."""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Central configuration loaded from environment variables."""

    # --- App ---
    app_env: str = "development"
    log_level: str = "INFO"
    app_title: str = "Discovery Engine API"
    app_version: str = "0.1.0"

    # --- PostgreSQL ---
    database_url: str = "postgresql://discovery:discovery_secret@localhost:5432/discovery_engine"

    # --- Redis ---
    redis_url: str = "redis://localhost:6379/0"

    # --- ChromaDB / Qdrant ---
    chroma_host: str = "localhost"
    chroma_port: int = 8000
    qdrant_url: str = "http://localhost:6333"

    # --- Groq LLM ---
    groq_api_key: str = ""
    groq_model: str = "openai/gpt-oss-120b"
    groq_temperature: float = 0.2
    groq_max_tokens: int = 4096

    # --- Embedding & Reranker ---
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    reranker_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"

    # --- Reddit ---
    reddit_client_id: str = ""
    reddit_client_secret: str = ""
    reddit_user_agent: str = "discovery-engine/1.0"

    # --- YouTube ---
    youtube_api_key: str = ""

    # --- Apify (Reddit scraper) ---
    apify_api_token: str = ""

    # --- CORS ---
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse comma-separated CORS origins into a list."""
        return [origin.strip() for origin in self.cors_origins.split(",")]

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore",
    }


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance — loaded once per process."""
    return Settings()
