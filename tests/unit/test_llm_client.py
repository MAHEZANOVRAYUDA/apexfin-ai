"""
Unit tests for LLM client implementations.
"""

import pytest

from src.domain.exceptions import ModelInferenceError, RateLimitExceededError
from src.generation.llm_client import DualLLMClient, MockLLMClient


@pytest.mark.asyncio
async def test_mock_llm_client_success():
    """Verify MockLLMClient returns valid json and identifier."""
    client = MockLLMClient()
    raw_json, model_name = await client.complete("sys", "user")
    assert model_name == "mock-llama-3.3-70b"
    assert "Net sales and revenue reached" in raw_json


@pytest.mark.asyncio
async def test_mock_llm_client_failure():
    """Verify MockLLMClient can simulate rate limit failures."""
    client = MockLLMClient(should_fail=True)
    with pytest.raises(RateLimitExceededError):
        await client.complete("sys", "user")


@pytest.mark.asyncio
async def test_dual_client_no_keys_raises_error():
    """Verify DualLLMClient rejects execution when no API keys are present."""
    client = DualLLMClient(groq_api_key=None, gemini_api_key=None)
    with pytest.raises(ModelInferenceError, match="No LLM credentials configured"):
        await client.complete("sys", "user")
