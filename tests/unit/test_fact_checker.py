"""
Unit tests for DeterministicFactChecker.
"""

import pytest

from src.domain.entities import (
    AnalysisReport,
    ChunkMetadata,
    CitationSource,
    DocumentChunk,
    FinancialMetric,
)
from src.domain.exceptions import VerificationFactCheckError
from src.generation.fact_checker import DeterministicFactChecker


def test_fact_checker_number_extraction():
    """Verify regex correctly isolates monetary and percentage figures."""
    text = "Operating cash flow was $110,543 million while net margin was 25.4%."
    numbers = DeterministicFactChecker.extract_numbers(text)
    assert any("110,543" in n for n in numbers)
    assert any("25.4%" in n for n in numbers)


def test_fact_checker_verified_numbers():
    """Verify report with accurate figures passes without warnings."""
    checker = DeterministicFactChecker()

    meta = ChunkMetadata(
        document_id="doc-1",
        document_name="apple.pdf",
        page_number=1,
        chunk_index=0,
    )
    chunk = DocumentChunk(
        content="Total net sales for fiscal 2023 were $383,285 million, compared to $394,328 million in 2022.",
        metadata=meta,
    )

    report = AnalysisReport(
        query="Apple revenue?",
        executive_summary="Apple achieved $383,285 million in net sales for fiscal year 2023.",
        extracted_metrics=[
            FinancialMetric(
                name="Net Sales",
                value=383285.0,
                unit="USD Millions",
                period="FY2023",
                context_sentence="Total net sales for fiscal 2023 were $383,285 million.",
            )
        ],
        citations=[
            CitationSource(
                document_name="apple.pdf",
                page_number=1,
                excerpt="Total net sales for fiscal 2023 were $383,285 million.",
                relevance_score=1.0,
            )
        ],
        confidence_score=0.95,
    )

    verified_report = checker.verify_report(report, [chunk], strict=False)
    assert len(verified_report.audit_warnings) == 0
    assert verified_report.confidence_score == 0.95


def test_fact_checker_catches_hallucinations():
    """Verify hallucinated figures generate audit warnings and decrease confidence."""
    checker = DeterministicFactChecker()

    meta = ChunkMetadata(
        document_id="doc-1",
        document_name="apple.pdf",
        page_number=1,
        chunk_index=0,
    )
    # The source only has $383,285
    chunk = DocumentChunk(
        content="Total net sales for fiscal 2023 were $383,285 million.",
        metadata=meta,
    )

    # The report hallucinates $500,000 million and 85%
    report = AnalysisReport(
        query="Apple revenue?",
        executive_summary="Apple achieved $500,000 million in revenue with an 85% gross margin.",
        citations=[
            CitationSource(
                document_name="apple.pdf",
                page_number=1,
                excerpt="Some excerpt",
                relevance_score=0.5,
            )
        ],
        confidence_score=0.90,
    )

    verified_report = checker.verify_report(report, [chunk], strict=False)
    assert len(verified_report.audit_warnings) >= 1
    assert "Unverified numerical figures detected" in verified_report.audit_warnings[0]
    # Confidence score should have dropped
    assert verified_report.confidence_score < 0.90


def test_fact_checker_strict_mode_raises_error():
    """Verify strict=True raises VerificationFactCheckError on hallucinations."""
    checker = DeterministicFactChecker()

    meta = ChunkMetadata(document_id="doc-1", document_name="doc.pdf", page_number=1, chunk_index=0)
    chunk = DocumentChunk(content="Net profit was $10 million.", metadata=meta)

    report = AnalysisReport(
        query="Profit?",
        executive_summary="Profit was $999 million.",  # Hallucinated
        citations=[
            CitationSource(
                document_name="doc.pdf", page_number=1, excerpt="text", relevance_score=0.5
            )
        ],
        confidence_score=0.9,
    )

    with pytest.raises(VerificationFactCheckError, match="Fact verification failed in strict mode"):
        checker.verify_report(report, [chunk], strict=True)
