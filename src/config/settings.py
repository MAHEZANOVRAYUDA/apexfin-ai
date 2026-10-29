"""
Configuration module for ApexFin AI using Pydantic Settings.
Enforces fail-fast validation of environment variables and application secrets.
"""

from functools import lru_cache
from typing import Any, Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Central application settings schema.
    Reads from environment variables and optional .env file.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )

    # Application Core
    ENVIRONMENT: Literal["development", "testing", "production"] = Field(
        default="development",
        description="Current runtime environment",
    )
    APP_HOST: str = Field(default="0.0.0.0", description="Host address for FastAPI server")
    APP_PORT: int = Field(default=8000, ge=1, le=65535, description="Port for FastAPI server")
    DEBUG: bool = Field(default=False, description="Debug mode flag")

    # LLM Providers (Free Tier Cloud Inference)
    GROQ_API_KEY: str | None = Field(
        default=None,
        description="Groq API Key for high-speed Llama-3.3-70B inference",
    )
    GROQ_MODEL: str = Field(
        default="openai/gpt-oss-120b",
        description="Default Groq LLM model identifier",
    )
    GEMINI_API_KEY: str | None = Field(
        default=None,
        description="Google Gemini API Key for high-context fallback inference",
    )
    GEMINI_MODEL: str = Field(
        default="gemini-3.8-flash",
        description="Default Google Gemini model identifier",
    )

    # Vector Storage (Qdrant)
    QDRANT_URL: str = Field(
        default=":memory:",
        description="Qdrant endpoint URL. Use ':memory:' for lightweight in-memory storage",
    )
    QDRANT_API_KEY: str | None = Field(
        default=None,
        description="API Key for Qdrant Cloud cluster",
    )
    QDRANT_COLLECTION_NAME: str = Field(
        default="financial_documents",
        description="Target collection name in Qdrant",
    )

    # Tracing & MLOps Observability (Langfuse)
    LANGFUSE_PUBLIC_KEY: str | None = Field(
        default=None,
        description="Langfuse public project key",
    )
    LANGFUSE_SECRET_KEY: str | None = Field(
        default=None,
        description="Langfuse secret project key",
    )
    LANGFUSE_HOST: str = Field(
        default="https://cloud.langfuse.com",
        description="Langfuse server host endpoint",
    )
    LANGFUSE_ENABLED: bool = Field(
        default=False,
        description="Enable/disable telemetry tracing",
    )

    # Guardrails & Ingestion Limits
    PROMPT_CANARY_SECRET: str = Field(
        default="apexfin-canary-audit-token-998",
        description="Secret nonce used to detect prompt leaks",
    )
    MAX_FILE_SIZE_MB: int = Field(
        default=25,
        ge=1,
        le=100,
        description="Maximum PDF upload size in Megabytes",
    )
    MAX_RETRIEVAL_CANDIDATES: int = Field(
        default=25,
        ge=5,
        le=100,
        description="Number of candidate chunks to retrieve from each search arm",
    )
    TOP_RERANK_LIMIT: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Number of high-relevance chunks forwarded to LLM synthesis",
    )

    @field_validator("ENVIRONMENT", mode="before")
    @classmethod
    def validate_environment(cls, v: Any) -> Any:
        if isinstance(v, str):
            return v.lower().strip()
        return v

    @model_validator(mode="after")
    def validate_production_keys(self) -> "Settings":
        """
        Enforce fail-fast secret validation when running in production.
        Prevents starting with missing inference credentials or unauthenticated remote DBs.
        """
        if self.ENVIRONMENT == "production":
            if not self.has_llm_credentials:
                raise ValueError(
                    "Production environment requires at least one LLM API key "
                    "(GROQ_API_KEY or GEMINI_API_KEY) to be configured."
                )
            if (
                self.QDRANT_URL != ":memory:"
                and not self.QDRANT_URL.startswith(("http://localhost", "http://127.0.0.1"))
                and not self.QDRANT_API_KEY
            ):
                raise ValueError(
                    "Cloud Qdrant deployment requires QDRANT_API_KEY to be configured in production."
                )
        return self

    @property
    def has_llm_credentials(self) -> bool:
        """Checks if at least one cloud LLM API key is configured with a real value."""

        def _is_valid(k: str | None) -> bool:
            return bool(k and not k.startswith("your_"))

        return _is_valid(self.GROQ_API_KEY) or _is_valid(self.GEMINI_API_KEY)


@lru_cache
def get_settings() -> Settings:
    """Returns singleton cached instance of Application Settings."""
    return Settings()
