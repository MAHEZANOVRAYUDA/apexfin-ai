"""
Table extraction and Markdown preservation engine for financial documents.
Converts coordinate-extracted PDF table matrices into standardized GitHub-flavored Markdown.
"""

import re

from pydantic import BaseModel, Field


class ExtractedTable(BaseModel):
    """Structured representation of an extracted financial table."""

    table_id: str = Field(description="Unique identifier for the table (e.g., tbl-p14-01)")
    page_number: int = Field(ge=1, description="1-indexed PDF page where table is located")
    bbox: tuple[float, float, float, float] = Field(
        description="Bounding box coordinates (x0, top, x1, bottom)"
    )
    markdown: str = Field(description="Formatted GitHub-flavored Markdown table")
    num_rows: int = Field(ge=1, description="Total non-empty rows in table")
    num_cols: int = Field(ge=1, description="Total columns in table")
    raw_rows: list[list[str]] = Field(
        default_factory=list,
        description="Cleaned cell matrix before Markdown formatting",
    )


class TableExtractor:
    """
    Transforms 2D raw cell grids from PDF tables into clean,
    deterministic Markdown matrices while preventing column fragmentation.
    """

    @staticmethod
    def clean_cell(cell: str | None) -> str:
        """Sanitizes individual cell text, handling line breaks and pipes."""
        if cell is None:
            return ""
        # Convert to string and strip outer whitespace
        cleaned = str(cell).strip()
        # Replace newlines with spaces to avoid breaking Markdown rows
        cleaned = re.sub(r"[\r\n]+", " ", cleaned)
        # Normalize multiple spaces
        cleaned = re.sub(r"\s{2,}", " ", cleaned)
        # Escape markdown pipe characters
        return cleaned.replace("|", r"\|")

    @classmethod
    def is_numeric_col(cls, values: list[str]) -> bool:
        """Determines if a column is predominantly numerical (currency/percentage/amount)."""
        if not values:
            return False
        num_pattern = re.compile(r"^(?:Rp|[\$€£¥])?\s*[\(\-]?\s*\d+(?:[,\.]\d+)*%?\s*[\)]?$")
        matches = sum(1 for v in values if v and num_pattern.match(v.strip()))
        return (matches / max(len(values), 1)) >= 0.5

    @classmethod
    def to_markdown(
        cls,
        raw_table: list[list[str | None]],
        table_id: str,
        page_number: int,
        bbox: tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.0),
    ) -> ExtractedTable | None:
        """
        Converts a 2D raw grid into an ExtractedTable with GitHub-flavored Markdown.
        Returns None if table has no meaningful content.
        """
        if not raw_table:
            return None

        # Clean all cells
        cleaned_rows: list[list[str]] = []
        max_cols = 0

        for row in raw_table:
            cleaned_row = [cls.clean_cell(cell) for cell in row]
            cleaned_rows.append(cleaned_row)
            if len(cleaned_row) > max_cols:
                max_cols = len(cleaned_row)

        if not cleaned_rows or max_cols == 0:
            return None

        # Pad rows to maintain uniform column count
        uniform_rows: list[list[str]] = []
        for row in cleaned_rows:
            if len(row) < max_cols:
                row = row + [""] * (max_cols - len(row))
            uniform_rows.append(row)

        # Ensure at least one cell has meaningful text
        has_content = any(any(cell for cell in row) for row in uniform_rows)
        if not has_content:
            return None

        # Header row extraction
        header_row = uniform_rows[0]
        if not any(header_row):
            header_row = [f"Col {i + 1}" for i in range(max_cols)]
            data_rows = [r for r in uniform_rows[1:] if any(r)]
        else:
            data_rows = [r for r in uniform_rows[1:] if any(r)]

        # Determine column alignments (right-align for numerical columns)
        alignments: list[str] = []
        for col_idx in range(max_cols):
            col_data = [r[col_idx] for r in data_rows]
            if cls.is_numeric_col(col_data):
                alignments.append("---:")  # Right align for financials
            else:
                alignments.append(":---")  # Left align for descriptions

        # Build Markdown
        md_lines: list[str] = []
        # Header line
        md_lines.append("| " + " | ".join(header_row) + " |")
        # Separator line
        md_lines.append("| " + " | ".join(alignments) + " |")
        # Data rows
        for row in data_rows:
            md_lines.append("| " + " | ".join(row) + " |")

        markdown_output = "\n".join(md_lines)
        total_rows = 1 + len(data_rows)

        return ExtractedTable(
            table_id=table_id,
            page_number=page_number,
            bbox=bbox,
            markdown=markdown_output,
            num_rows=total_rows,
            num_cols=max_cols,
            raw_rows=[header_row] + data_rows,
        )
