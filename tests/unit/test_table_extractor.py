"""
Unit tests for TableExtractor and Markdown preservation in ApexFin AI.
"""

from src.ingestion.table_extractor import TableExtractor


def test_clean_cell():
    """Verify cell sanitization strips newlines, spaces, and escapes pipes."""
    assert TableExtractor.clean_cell("  Revenue \n (USD)  ") == "Revenue (USD)"
    assert TableExtractor.clean_cell("Assets | Liabilities") == r"Assets \| Liabilities"
    assert TableExtractor.clean_cell(None) == ""
    assert TableExtractor.clean_cell("123\r\n456") == "123 456"


def test_is_numeric_col():
    """Verify heuristic detection of financial/numerical columns."""
    financial_nums = ["$10,500", "($450)", "78.4%", "1,200,000"]
    assert TableExtractor.is_numeric_col(financial_nums) is True

    text_col = ["Operating Cash Flow", "Capital Expenditures", "Free Cash Flow"]
    assert TableExtractor.is_numeric_col(text_col) is False


def test_to_markdown_valid_financial_table():
    """Verify 2D matrix transformation to GitHub-flavored Markdown."""
    raw_data = [
        ["Line Item", "FY2022", "FY2023"],
        ["Total Net Sales", "$394,328", "$383,285"],
        ["Net Income", "$99,803", "$96,995"],
    ]
    table = TableExtractor.to_markdown(
        raw_table=raw_data,
        table_id="tbl-p10-01",
        page_number=10,
        bbox=(50.0, 100.0, 500.0, 250.0),
    )
    assert table is not None
    assert table.table_id == "tbl-p10-01"
    assert table.page_number == 10
    assert table.num_rows == 3
    assert table.num_cols == 3
    assert "| Line Item | FY2022 | FY2023 |" in table.markdown
    assert "---:" in table.markdown  # Numerical column right alignment
    assert "| Total Net Sales | $394,328 | $383,285 |" in table.markdown


def test_to_markdown_pads_uneven_rows():
    """Verify rows with fewer columns are padded with empty cells."""
    raw_data = [
        ["Col1", "Col2", "Col3"],
        ["Short Row"],
        ["Full Row 1", "Full Row 2", "Full Row 3"],
    ]
    table = TableExtractor.to_markdown(raw_data, table_id="tbl-01", page_number=1)
    assert table is not None
    assert table.num_cols == 3
    assert "| Short Row |  |  |" in table.markdown


def test_to_markdown_empty_or_whitespace():
    """Verify empty grid returns None."""
    assert TableExtractor.to_markdown([], table_id="tbl-0", page_number=1) is None
    assert (
        TableExtractor.to_markdown([[" ", "   "], [None, ""]], table_id="tbl-0", page_number=1)
        is None
    )


def test_to_markdown_empty_header_synthesizes_labels():
    """Verify empty top header generates Col 1, Col 2 labels."""
    raw_data = [
        ["", ""],
        ["Row1", "Data1"],
    ]
    table = TableExtractor.to_markdown(raw_data, table_id="tbl-02", page_number=1)
    assert table is not None
    assert "| Col 1 | Col 2 |" in table.markdown
