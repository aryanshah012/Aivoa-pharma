"""Application settings loaded from environment variables / .env file.

No secrets are hardcoded anywhere in the codebase.
"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Database
    DATABASE_URL: str = "sqlite:///./pharmaqms.db"

    # LLM
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "gemma2-9b-it"
    GROQ_FALLBACK_MODEL: str = "llama-3.3-70b-versatile"
    LLM_MAX_TOKENS: int = 1024
    LLM_TEMPERATURE: float = 0.1
    LLM_REQUEST_TIMEOUT: int = 60

    # CORS
    FRONTEND_URL: str = "http://localhost:5173"
    CORS_ORIGINS: str = "http://localhost:5173"

    # Uploads
    MAX_UPLOAD_MB: int = 10

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def llm_models(self) -> list[str]:
        """Primary model first, fallback model second, de-duplicated."""
        models = [self.GROQ_MODEL, self.GROQ_FALLBACK_MODEL]
        seen: list[str] = []
        for m in models:
            if m and m not in seen:
                seen.append(m)
        return seen


@lru_cache
def get_settings() -> Settings:
    return Settings()
