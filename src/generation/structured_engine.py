"""
Structured Generation Engine with Pydantic validation and canary defense for ApexFin AI.
Enforces guaranteed contract outputs and mitigates prompt injection risks.
"""

import time

from src.config.settings import get_settings
from src.domain.entities import AnalysisReport, DocumentChunk
from src.domain.exceptions import ModelInferenceError, PromptInjectionDetectedError
from src.generation.llm_client import BaseLLMClient, DualLLMClient
from src.generation.prompts import FinancialPromptBuilder


class StructuredGenerationEngine:
    """
    Coordinates LLM inference, canary security checks, and strict Pydantic v2
    schema validation for audit-ready financial analysis reports.
    """

    def __init__(
        self,
        llm_client: BaseLLMClient | None = None,
        prompt_builder: FinancialPromptBuilder | None = None,
        canary_secret: str | None = None,
    ):
        settings = get_settings()
        self.llm_client = llm_client or DualLLMClient()
        self.prompt_builder = prompt_builder or FinancialPromptBuilder(canary_secret=canary_secret)
        self.canary_secret = canary_secret or settings.PROMPT_CANARY_SECRET

    def _detect_prompt_injection(self, text: str) -> None:
        """Inspects input for obvious jailbreak or delimiter tampering patterns."""
        dangerous_patterns = [
            "ignore previous instructions",
            "ignore all prior instructions",
            "system prompt leak",
            "reveal the canary",
            "</retrieved_evidence>",
            "</user_query>",
        ]
        text_lower = text.lower()
        for pattern in dangerous_patterns:
            if pattern in text_lower:
                raise PromptInjectionDetectedError(
                    f"Rejected suspicious input pattern: '{pattern}'"
                )

    async def generate_analysis(
        self,
        query: str,
        retrieved_chunks: list[DocumentChunk],
    ) -> AnalysisReport:
        """
        Executes safe generation pipeline:
        1. Pre-flight input sanitizer
        2. Prompt construction with XML encapsulation & canary nonce
        3. LLM completion via Groq / Gemini Flash
        4. Post-flight canary leak verification
        5. Pydantic schema validation into AnalysisReport
        """
        start_time = time.perf_counter()

        # 1. Pre-flight check
        self._detect_prompt_injection(query)

        # 2. Build isolated prompts
        system_prompt = self.prompt_builder.build_system_prompt()
        user_prompt = self.prompt_builder.build_user_prompt(query=query, chunks=retrieved_chunks)

        # 3. Complete inference
        raw_json, model_name = await self.llm_client.complete(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )

        # 4. Post-flight canary leak verification
        if self.canary_secret and self.canary_secret in raw_json:
            raise PromptInjectionDetectedError(
                "Adversarial attack detected: Canary secret token was leaked in model completion."
            )

        # 5. Pydantic validation with schema fallback resilience
        import json

        try:
            data = json.loads(raw_json)
            # If citations list is empty (e.g. LLM determined evidence lacks answer),
            # attach an audit trail citation to preserve contract integrity
            if isinstance(data, dict) and not data.get("citations"):
                fallback_doc = (
                    retrieved_chunks[0].metadata.document_name
                    if retrieved_chunks
                    else "Dokumen Sumber"
                )
                fallback_page = (
                    retrieved_chunks[0].metadata.page_number if retrieved_chunks else 1
                )
                data["citations"] = [
                    {
                        "document_name": fallback_doc,
                        "page_number": fallback_page,
                        "is_table": False,
                        "excerpt": "Informasi spesifik tidak ditemukan pada dokumen sumber yang dianalisis.",
                        "relevance_score": 0.0,
                    }
                ]
                raw_json = json.dumps(data)

            report = AnalysisReport.model_validate_json(raw_json)
        except Exception as parse_exc:
            raise ModelInferenceError(
                model_name,
                f"LLM produced invalid JSON schema not conforming to AnalysisReport: {parse_exc!s}\nRaw: {raw_json[:300]}",
            ) from parse_exc

        duration_ms = (time.perf_counter() - start_time) * 1000.0
        report.query = query
        report.model_used = model_name
        report.processing_time_ms = round(duration_ms, 2)

        return report
