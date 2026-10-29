"""
Unit tests for RFC 7807 Problem Details and Domain Exceptions in ApexFin AI.
"""

from src.domain.exceptions import (
    ApexFinException,
    DocumentNotFoundError,
    DocumentParsingError,
    ModelInferenceError,
    ProblemDetails,
    PromptInjectionDetectedError,
    RateLimitExceededError,
    VerificationFactCheckError,
)


def test_problem_details_schema():
    """Verify ProblemDetails conforms to RFC 7807 contract."""
    pd = ProblemDetails(
        type="https://apexfin.ai/errors/sample",
        title="Sample Error",
        status=400,
        detail="Something went wrong with your query parameter.",
        instance="/api/v1/query?q=error",
        invalid_params=[{"name": "q", "reason": "Query string too long"}],
    )
    dumped = pd.model_dump()
    assert dumped["type"] == "https://apexfin.ai/errors/sample"
    assert dumped["title"] == "Sample Error"
    assert dumped["status"] == 400
    assert dumped["detail"] == "Something went wrong with your query parameter."
    assert dumped["instance"] == "/api/v1/query?q=error"
    assert len(dumped["invalid_params"]) == 1


def test_base_apexfin_exception():
    """Verify base ApexFinException converts to ProblemDetails."""
    exc = ApexFinException(
        detail="Unexpected database lock.",
        title="Storage Failure",
        status_code=503,
        type_uri="https://apexfin.ai/errors/storage",
    )
    pd = exc.to_problem_details(instance="/api/v1/documents")
    assert pd.status == 503
    assert pd.title == "Storage Failure"
    assert pd.detail == "Unexpected database lock."
    assert pd.instance == "/api/v1/documents"


def test_document_parsing_error():
    """Verify DocumentParsingError produces 422 ProblemDetails."""
    err = DocumentParsingError("Corrupt xref table at byte 4096.")
    assert err.status_code == 422
    pd = err.to_problem_details()
    assert pd.status == 422
    assert pd.title == "Document Parsing Failed"
    assert "Corrupt xref table" in pd.detail
    assert pd.type == "https://apexfin.ai/errors/document-parsing"


def test_document_not_found_error():
    """Verify DocumentNotFoundError produces 404 ProblemDetails."""
    err = DocumentNotFoundError("doc-missing-123")
    assert err.status_code == 404
    pd = err.to_problem_details()
    assert pd.status == 404
    assert pd.title == "Document Not Found"
    assert "doc-missing-123" in pd.detail
    assert pd.type == "https://apexfin.ai/errors/document-not-found"


def test_model_inference_error():
    """Verify ModelInferenceError produces 502 ProblemDetails."""
    err = ModelInferenceError("Groq", "Connection timed out after 10000ms")
    assert err.status_code == 502
    pd = err.to_problem_details()
    assert pd.status == 502
    assert pd.title == "Model Inference Error"
    assert "Groq" in pd.detail
    assert pd.type == "https://apexfin.ai/errors/model-inference"


def test_rate_limit_exceeded_error():
    """Verify RateLimitExceededError produces 429 ProblemDetails."""
    err = RateLimitExceededError()
    assert err.status_code == 429
    pd = err.to_problem_details()
    assert pd.status == 429
    assert pd.title == "Rate Limit Exceeded"
    assert pd.type == "https://apexfin.ai/errors/rate-limit"


def test_prompt_injection_detected_error():
    """Verify PromptInjectionDetectedError produces 400 ProblemDetails."""
    err = PromptInjectionDetectedError("Canary token revealed.")
    assert err.status_code == 400
    pd = err.to_problem_details()
    assert pd.status == 400
    assert pd.title == "Adversarial Input Rejected"
    assert pd.type == "https://apexfin.ai/errors/prompt-injection"


def test_verification_fact_check_error():
    """Verify VerificationFactCheckError produces 422 ProblemDetails."""
    err = VerificationFactCheckError("Claimed $400B revenue not found in source text.")
    assert err.status_code == 422
    pd = err.to_problem_details()
    assert pd.status == 422
    assert pd.title == "Numerical Fact Verification Failed"
    assert pd.type == "https://apexfin.ai/errors/fact-verification"
