"""
Domain Exceptions & RFC 7807 Problem Details for ApexFin AI.
Standardizes international HTTP API error representations.
"""

from typing import Any

from pydantic import BaseModel, Field


class ProblemDetails(BaseModel):
    """
    RFC 7807 Standard Error Envelope.
    Provides human-readable explanation and machine-readable error classification.
    """

    type: str = Field(
        default="about:blank",
        description="A URI reference that identifies the problem type",
    )
    title: str = Field(description="A short, human-readable summary of the problem type")
    status: int = Field(description="The HTTP status code applicable to this problem")
    detail: str = Field(description="A human-readable explanation specific to this occurrence")
    instance: str | None = Field(
        default=None,
        description="A URI reference that identifies the specific occurrence of the problem",
    )
    invalid_params: list[dict[str, Any]] | None = Field(
        default=None,
        description="Details about individual query/body parameters that failed validation",
    )


class ApexFinException(Exception):  # noqa: N818
    """Base exception for all ApexFin AI domain failures."""

    def __init__(
        self,
        detail: str,
        title: str = "Internal Application Error",
        status_code: int = 500,
        type_uri: str = "https://apexfin.ai/errors/internal",
    ):
        super().__init__(detail)
        self.detail = detail
        self.title = title
        self.status_code = status_code
        self.type_uri = type_uri

    def to_problem_details(self, instance: str | None = None) -> ProblemDetails:
        return ProblemDetails(
            type=self.type_uri,
            title=self.title,
            status=self.status_code,
            detail=self.detail,
            instance=instance,
        )


class DocumentParsingError(ApexFinException):
    """Raised when PDF document structure is corrupt or unreadable."""

    def __init__(self, detail: str):
        super().__init__(
            detail=detail,
            title="Document Parsing Failed",
            status_code=422,
            type_uri="https://apexfin.ai/errors/document-parsing",
        )


class DocumentNotFoundError(ApexFinException):
    """Raised when target document ID does not exist in vector index."""

    def __init__(self, document_id: str):
        super().__init__(
            detail=f"Financial document with ID '{document_id}' was not found in the index.",
            title="Document Not Found",
            status_code=404,
            type_uri="https://apexfin.ai/errors/document-not-found",
        )


class ModelInferenceError(ApexFinException):
    """Raised when upstream LLM API returns unrecoverable error."""

    def __init__(self, provider: str, detail: str):
        super().__init__(
            detail=f"Inference provider '{provider}' failed: {detail}",
            title="Model Inference Error",
            status_code=502,
            type_uri="https://apexfin.ai/errors/model-inference",
        )


class RateLimitExceededError(ApexFinException):
    """Raised when all LLM providers exceed rate limits."""

    def __init__(self, detail: str = "All free-tier LLM quotas exhausted. Please retry shortly."):
        super().__init__(
            detail=detail,
            title="Rate Limit Exceeded",
            status_code=429,
            type_uri="https://apexfin.ai/errors/rate-limit",
        )


class PromptInjectionDetectedError(ApexFinException):
    """Raised when canary tokens or adversarial patterns are triggered."""

    def __init__(self, detail: str = "Malicious prompt injection or delimiter tampering detected."):
        super().__init__(
            detail=detail,
            title="Adversarial Input Rejected",
            status_code=400,
            type_uri="https://apexfin.ai/errors/prompt-injection",
        )


class VerificationFactCheckError(ApexFinException):
    """Raised when numbers in synthesis fail verbatim check against source."""

    def __init__(self, detail: str):
        super().__init__(
            detail=detail,
            title="Numerical Fact Verification Failed",
            status_code=422,
            type_uri="https://apexfin.ai/errors/fact-verification",
        )
