"""
Unit tests for Settings configuration and fail-fast validation in ApexFin AI.
"""

import pytest
from pydantic import ValidationError

from src.config.settings import Settings, get_settings


def test_default_settings():
    """Verify default development configuration."""
    settings = Settings(
        ENVIRONMENT="development",
        GROQ_API_KEY=None,
        GEMINI_API_KEY=None,
    )
    assert settings.ENVIRONMENT == "development"
    assert settings.APP_HOST == "0.0.0.0"
    assert settings.APP_PORT == 8000
    assert settings.DEBUG is False
    assert settings.QDRANT_URL == ":memory:"
    assert settings.has_llm_credentials is False
    assert settings.MAX_FILE_SIZE_MB == 25
    assert settings.TOP_RERANK_LIMIT == 5


def test_has_llm_credentials():
    """Verify credentials check property."""
    s_none = Settings(ENVIRONMENT="development", GROQ_API_KEY=None, GEMINI_API_KEY=None)
    assert s_none.has_llm_credentials is False

    s_groq = Settings(ENVIRONMENT="development", GROQ_API_KEY="gsk_dummy", GEMINI_API_KEY=None)
    assert s_groq.has_llm_credentials is True

    s_gemini = Settings(ENVIRONMENT="development", GROQ_API_KEY=None, GEMINI_API_KEY="AIza_dummy")
    assert s_gemini.has_llm_credentials is True


def test_environment_normalization():
    """Verify case normalization for environment."""
    s = Settings(ENVIRONMENT="DEVELOPMENT", GROQ_API_KEY=None, GEMINI_API_KEY=None)
    assert s.ENVIRONMENT == "development"


def test_production_fail_fast_missing_llm_keys():
    """Verify production rejects startup if no LLM keys are configured."""
    with pytest.raises(
        ValidationError, match="Production environment requires at least one LLM API key"
    ):
        Settings(
            ENVIRONMENT="production",
            GROQ_API_KEY=None,
            GEMINI_API_KEY=None,
        )


def test_production_fail_fast_missing_qdrant_key():
    """Verify production rejects startup if remote Qdrant has no API key."""
    with pytest.raises(ValidationError, match="Cloud Qdrant deployment requires QDRANT_API_KEY"):
        Settings(
            ENVIRONMENT="production",
            GROQ_API_KEY="gsk_dummy_key",
            QDRANT_URL="https://qdrant-xyz.cloud.qdrant.io:6333",
            QDRANT_API_KEY=None,
        )


def test_production_valid_configuration():
    """Verify production accepts valid LLM credentials and in-memory or authenticated Qdrant."""
    s_memory = Settings(
        ENVIRONMENT="production",
        GROQ_API_KEY="gsk_test_key",
        QDRANT_URL=":memory:",
    )
    assert s_memory.ENVIRONMENT == "production"

    s_cloud = Settings(
        ENVIRONMENT="production",
        GEMINI_API_KEY="AIza_test_key",
        QDRANT_URL="https://qdrant-xyz.cloud.qdrant.io:6333",
        QDRANT_API_KEY="qdrant_valid_key",
    )
    assert s_cloud.ENVIRONMENT == "production"


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("APP_PORT", 0),
        ("APP_PORT", 70000),
        ("MAX_FILE_SIZE_MB", 0),
        ("MAX_FILE_SIZE_MB", 150),
        ("MAX_RETRIEVAL_CANDIDATES", 2),
        ("MAX_RETRIEVAL_CANDIDATES", 200),
        ("TOP_RERANK_LIMIT", 0),
        ("TOP_RERANK_LIMIT", 50),
    ],
)
def test_boundary_validation_constraints(field: str, bad_value: int):
    """Verify numerical boundary checks on operational limits."""
    kwargs = {field: bad_value}
    with pytest.raises(ValidationError):
        Settings(**kwargs)


def test_get_settings_cached_singleton():
    """Verify get_settings returns singleton instance."""
    s1 = get_settings()
    s2 = get_settings()
    assert s1 is s2
