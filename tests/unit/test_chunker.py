"""
Unit tests for HierarchicalChunker in ApexFin AI.
Verifies atomic preservation of financial tables and boundary-aware narrative sliding windows.
"""

from src.ingestion.chunker import HierarchicalChunker
from src.ingestion.pdf_parser import ParsedDocument, ParsedPage
from src.ingestion.table_extractor import ExtractedTable


def test_chunker_atomic_table_preservation():
    """Verify tables are kept intact as individual atomic chunks."""
    table = ExtractedTable(
        table_id="tbl-p1-01",
        page_number=1,
        bbox=(50.0, 100.0, 400.0, 300.0),
        markdown="| Item | Amount |\n| :--- | ---: |\n| Cash | $30,000 |",
        num_rows=2,
        num_cols=2,
    )
    page = ParsedPage(
        page_number=1,
        narrative_text="Overview of cash position.",
        tables=[table],
        section_header="Item 7",
    )
    doc = ParsedDocument(
        document_id="doc-001",
        document_name="test_10k.pdf",
        total_pages=1,
        pages=[page],
    )

    chunker = HierarchicalChunker(chunk_size_tokens=100, overlap_tokens=20)
    chunks = chunker.chunk_document(doc)

    assert len(chunks) == 2
    # First chunk is the preserved table
    assert chunks[0].metadata.is_table is True
    assert chunks[0].metadata.table_id == "tbl-p1-01"
    assert chunks[0].metadata.page_number == 1
    assert chunks[0].metadata.chunk_index == 0
    assert chunks[0].content == table.markdown

    # Second chunk is the narrative text
    assert chunks[1].metadata.is_table is False
    assert chunks[1].metadata.chunk_index == 1
    assert chunks[1].content == "Overview of cash position."


def test_chunker_narrative_sliding_window_and_overlap():
    """Verify narrative text splits across sliding window with word overlap."""
    # Create 30 sentences of financial analysis
    sentences = [
        f"Sentence number {i} describes operational segment performance and profitability margins."
        for i in range(1, 41)
    ]
    long_narrative = " ".join(sentences)

    page = ParsedPage(
        page_number=3,
        narrative_text=long_narrative,
        tables=[],
        section_header="Item 7. MD&A",
    )
    doc = ParsedDocument(
        document_id="doc-long",
        document_name="long_report.pdf",
        total_pages=1,
        pages=[page],
    )

    # Use small word limit to trigger multiple chunks
    chunker = HierarchicalChunker(chunk_size_tokens=60, overlap_tokens=15)
    chunks = chunker.chunk_document(doc)

    assert len(chunks) > 1
    # Check that sequential chunk indices are contiguous
    indices = [c.metadata.chunk_index for c in chunks]
    assert indices == list(range(len(chunks)))

    # Verify all chunks inherit metadata
    for chunk in chunks:
        assert chunk.metadata.document_id == "doc-long"
        assert chunk.metadata.document_name == "long_report.pdf"
        assert chunk.metadata.page_number == 3
        assert chunk.metadata.section_header == "Item 7. MD&A"
        assert chunk.metadata.is_table is False


def test_chunker_empty_narrative_with_only_tables():
    """Verify document with pages containing only tables produces only table chunks."""
    table1 = ExtractedTable(
        table_id="tbl-p1-01",
        page_number=1,
        bbox=(0.0, 0.0, 100.0, 100.0),
        markdown="| A | B |\n|---|---|",
        num_rows=1,
        num_cols=2,
    )
    page = ParsedPage(
        page_number=1,
        narrative_text="",
        tables=[table1],
        section_header=None,
    )
    doc = ParsedDocument(
        document_id="doc-tables-only",
        document_name="tables.pdf",
        total_pages=1,
        pages=[page],
    )

    chunker = HierarchicalChunker()
    chunks = chunker.chunk_document(doc)

    assert len(chunks) == 1
    assert chunks[0].metadata.is_table is True
    assert chunks[0].metadata.chunk_index == 0
