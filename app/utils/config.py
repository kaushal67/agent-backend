"""Application settings and environment variable management."""

from __future__ import annotations

import os
from functools import lru_cache
from typing import List, Optional

from dotenv import load_dotenv
from pydantic import BaseModel, Field, field_validator


load_dotenv()


class Settings(BaseModel):
    """Typed runtime configuration loaded from environment variables."""

    app_name: str = Field(default="AgriTriageAgent")
    app_env: str = Field(default="development")
    log_level: str = Field(default="INFO")
    database_url: str = Field(default="sqlite:///./agri_ai.db")
    cors_origins: str = Field(default="http://localhost:5173,http://127.0.0.1:5173")
    groq_api_key: Optional[str] = Field(default=None)
    openai_api_key: Optional[str] = Field(default=None)
    google_api_key: Optional[str] = Field(default=None)
    openweather_api_key: Optional[str] = Field(default=None)
    langchain_model: str = Field(default="llama-3.1-8b-instant")
    crewai_llm: str = Field(default="groq/llama-3.1-8b-instant")
    crewai_verbose: bool = Field(default=False)
    request_timeout_seconds: int = Field(default=25, ge=5, le=120)

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, value: str) -> str:
        """Normalize unsupported log levels to INFO."""
        allowed = {"CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"}
        normalized = (value or "INFO").upper()
        return normalized if normalized in allowed else "INFO"

    @property
    def cors_origins_list(self) -> List[str]:
        """Return parsed CORS origins from CSV configuration."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def has_llm_credentials(self) -> bool:
        """Return whether any supported LLM provider credential exists."""
        return bool(self.groq_api_key or self.openai_api_key or self.google_api_key)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Load and cache application settings from environment variables."""
    data = {
        "app_name": os.getenv("APP_NAME", "AgriTriageAgent"),
        "app_env": os.getenv("APP_ENV", "development"),
        "log_level": os.getenv("LOG_LEVEL", "INFO"),
        "database_url": os.getenv("DATABASE_URL", "sqlite:///./agri_ai.db"),
        "cors_origins": os.getenv(
            "CORS_ORIGINS",
            "http://localhost:5173,http://127.0.0.1:5173",
        ),
        "groq_api_key": os.getenv("GROQ_API_KEY"),
        "openai_api_key": os.getenv("OPENAI_API_KEY"),
        "google_api_key": os.getenv("GOOGLE_API_KEY"),
        "openweather_api_key": os.getenv("OPENWEATHER_API_KEY"),
        "langchain_model": os.getenv("LANGCHAIN_MODEL", "llama-3.1-8b-instant"),
        "crewai_llm": os.getenv("CREWAI_LLM", "groq/llama-3.1-8b-instant"),
        "crewai_verbose": os.getenv("CREWAI_VERBOSE", "false").strip().lower() == "true",
        "request_timeout_seconds": int(os.getenv("REQUEST_TIMEOUT_SECONDS", "25")),
    }
    return Settings.model_validate(data)
