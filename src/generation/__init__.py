"""
Generation module containing LLM failover adapters, XML prompt guardrails, and fact-checking.
"""

from src.generation.fact_checker import DeterministicFactChecker
from src.generation.llm_client import BaseLLMClient, DualLLMClient, MockLLMClient
from src.generation.prompts import FinancialPromptBuilder
from src.generation.structured_engine import StructuredGenerationEngine

__all__ = [
    "BaseLLMClient",
    "DeterministicFactChecker",
    "DualLLMClient",
    "FinancialPromptBuilder",
    "MockLLMClient",
    "StructuredGenerationEngine",
]
