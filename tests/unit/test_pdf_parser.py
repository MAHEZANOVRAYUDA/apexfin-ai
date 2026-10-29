"""
Unit tests for coordinate-aware PDFParser in ApexFin AI.
Generates synthetic in-memory PDFs using PyMuPDF to test parsing deterministically.
"""

from pathlib import Path

import fitz
import pytest

from src.domain.exceptions import DocumentParsingError
from src.ingestion.pdf_parser import PDFParser


def create_mock_financial_pdf() -> bytes:
    """Generates a valid 2-page financial PDF with headers, narrative, and drawn table."""
    doc = fitz.open()

    # Page 1: Header + Narrative + Drawn Table
    p1 = doc.new_page(width=595, height=842)
    p1.insert_text((50, 50), "ITEM 7. MANAGEMENT'S DISCUSSION AND ANALYSIS", fontsize=12)
    p1.insert_text(
        (50, 80),
        "During fiscal 2023, our total net sales decreased by 2.8% due to macroeconomic headwinds.",
        fontsize=10,
    )

    # Draw table bounding box and grid lines
    p1.draw_rect(fitz.Rect(50, 120, 450, 220))
    p1.draw_line(fitz.Point(50, 150), fitz.Point(450, 150))
    p1.draw_line(fitz.Point(250, 120), fitz.Point(250, 220))
    # Table text
    p1.insert_text((60, 140), "Product Segment", fontsize=10)
    p1.insert_text((260, 140), "Net Revenue (USD Millions)", fontsize=10)
    p1.insert_text((60, 180), "Data Center", fontsize=10)
    p1.insert_text((260, 180), "$18,400", fontsize=10)

    # Narrative below table
    p1.insert_text(
        (50, 260),
        "Data Center revenue demonstrated unprecedented customer demand across enterprise clusters.",
        fontsize=10,
    )

    # Page 2: Note section
    p2 = doc.new_page(width=595, height=842)
    p2.insert_text((50, 50), "NOTE 1 - SUMMARY OF SIGNIFICANT ACCOUNTING POLICIES", fontsize=12)
    p2.insert_text(
        (50, 80),
        "The accompanying financial statements have been prepared in accordance with US GAAP.",
        fontsize=10,
    )

    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def test_pdf_parser_bytes_success():
    """Verify in-memory PDF parsing extracts pages, narrative, and tables."""
    pdf_bytes = create_mock_financial_pdf()
    parser = PDFParser()
    parsed_doc = parser.parse_bytes(
        pdf_bytes=pdf_bytes,
        filename="mock_10k.pdf",
        document_id="doc-test-10k",
    )

    assert parsed_doc.document_id == "doc-test-10k"
    assert parsed_doc.document_name == "mock_10k.pdf"
    assert parsed_doc.total_pages == 2

    # Page 1 checks
    p1 = parsed_doc.pages[0]
    assert p1.page_number == 1
    assert "ITEM 7. MANAGEMENT'S DISCUSSION AND ANALYSIS" in p1.section_header
    assert "During fiscal 2023" in p1.narrative_text
    assert len(p1.tables) >= 1
    assert "| Product Segment | Net Revenue (USD Millions) |" in p1.tables[0].markdown

    # Page 2 checks
    p2 = parsed_doc.pages[1]
    assert p2.page_number == 2
    assert "NOTE 1" in p2.section_header
    assert "US GAAP" in p2.narrative_text


def test_pdf_parser_local_file(tmp_path: Path):
    """Verify local disk file parsing."""
    pdf_bytes = create_mock_financial_pdf()
    file_path = tmp_path / "apple_sample_10k.pdf"
    file_path.write_bytes(pdf_bytes)

    parser = PDFParser()
    doc = parser.parse_file(file_path)
    assert doc.document_name == "apple_sample_10k.pdf"
    assert doc.total_pages == 2


def test_pdf_parser_empty_bytes_fails():
    """Verify empty byte buffer raises DocumentParsingError."""
    parser = PDFParser()
    with pytest.raises(DocumentParsingError, match="empty PDF"):
        parser.parse_bytes(b"")


def test_pdf_parser_file_not_found():
    """Verify non-existent path raises DocumentParsingError."""
    parser = PDFParser()
    with pytest.raises(DocumentParsingError, match="File not found"):
        parser.parse_file("non_existent_financial_report.pdf")


def test_pdf_parser_corrupt_data():
    """Verify corrupt bytes raise DocumentParsingError."""
    parser = PDFParser()
    with pytest.raises(DocumentParsingError, match="Failed to parse PDF"):
        parser.parse_bytes(b"This is not a real PDF file contents 123456")
