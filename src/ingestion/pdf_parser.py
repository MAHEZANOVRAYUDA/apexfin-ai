"""
Coordinate-aware PDF parser for financial reports using pdfplumber.
Extracts narrative text and isolates financial tables into structured Markdown.
"""

import io
import re
import uuid
from functools import partial
from pathlib import Path

import pdfplumber
from pydantic import BaseModel, Field

from src.config.settings import get_settings
from src.domain.exceptions import DocumentParsingError
from src.ingestion.table_extractor import ExtractedTable, TableExtractor


class ParsedPage(BaseModel):
    """Encapsulates extracted narrative and isolated tables for a single PDF page."""

    page_number: int = Field(ge=1, description="1-indexed page number")
    narrative_text: str = Field(description="Pure narrative text excluding table cells")
    tables: list[ExtractedTable] = Field(default_factory=list, description="Isolated tables")
    section_header: str | None = Field(default=None, description="Current detected section header")


class ParsedDocument(BaseModel):
    """Full document representation containing all parsed pages."""

    document_id: str = Field(description="Unique document identifier")
    document_name: str = Field(description="Original filename")
    total_pages: int = Field(ge=1, description="Total pages processed")
    pages: list[ParsedPage] = Field(default_factory=list)


class PDFParser:
    """
    Coordinate-aware PDF parser designed for SEC 10-K, 10-Q, and annual financial statements.
    Ensures zero table shredding and clean text-table separation.
    """

    # Common financial report section patterns (SEC 10-K / IFRS)
    SECTION_PATTERN = re.compile(
        r"^(?:ITEM\s+[0-9A-Z]+[\.\:\-]?\s*.+|"
        r"NOTE\s+[0-9]+[\.\:\-]?\s*.+|"
        r"CONSOLIDATED\s+STATEMENTS?\s+OF\s+.+|"
        r"MANAGEMENT'S\s+DISCUSSION\s+AND\s+ANALYSIS.*|"
        r"PART\s+[I|V|X]+[\.\:\-]?\s*.+)",
        re.IGNORECASE,
    )

    def __init__(self, max_file_size_mb: int | None = None):
        settings = get_settings()
        self.max_file_size_mb = max_file_size_mb or settings.MAX_FILE_SIZE_MB

    @staticmethod
    def is_outside_tables(obj: dict, bboxes: tuple[tuple[float, float, float, float], ...]) -> bool:
        """Determines whether a PDF layout object lies outside all extracted table bboxes."""
        x0 = obj.get("x0", 0)
        top = obj.get("top", 0)
        x1 = obj.get("x1", 0)
        bottom = obj.get("bottom", 0)
        return all(x1 <= tb[0] or x0 >= tb[2] or bottom <= tb[1] or top >= tb[3] for tb in bboxes)

    def _detect_section_header(self, text: str, current_header: str | None) -> str | None:
        """Identifies prominent financial section headers from page lines."""
        for line in text.split("\n"):
            stripped = line.strip()
            if 4 <= len(stripped) <= 120 and self.SECTION_PATTERN.match(stripped):
                return stripped
        return current_header

    def parse_bytes(
        self,
        pdf_bytes: bytes,
        filename: str = "document.pdf",
        document_id: str | None = None,
    ) -> ParsedDocument:
        """Parses in-memory PDF bytes into a ParsedDocument."""
        if not pdf_bytes:
            raise DocumentParsingError("Cannot parse empty PDF byte buffer.")

        size_mb = len(pdf_bytes) / (1024 * 1024)
        if size_mb > self.max_file_size_mb:
            raise DocumentParsingError(
                f"PDF size ({size_mb:.1f} MB) exceeds maximum allowed limit of {self.max_file_size_mb} MB."
            )

        doc_id = document_id or str(uuid.uuid4())
        parsed_pages: list[ParsedPage] = []
        current_section: str | None = None

        try:
            with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
                total_pages = len(pdf.pages)
                if total_pages == 0:
                    raise DocumentParsingError("PDF contains zero pages.")

                for page_idx, page in enumerate(pdf.pages):
                    page_num = page_idx + 1

                    # 1. Extract and preserve tables with coordinates
                    extracted_tables: list[ExtractedTable] = []
                    table_bboxes: list[tuple[float, float, float, float]] = []

                    found_tables = page.find_tables()
                    for t_idx, found_t in enumerate(found_tables):
                        raw_matrix = found_t.extract()
                        if raw_matrix:
                            tbl_id = f"tbl-p{page_num}-{t_idx + 1:02d}"
                            tbl_bbox = (
                                float(found_t.bbox[0]),
                                float(found_t.bbox[1]),
                                float(found_t.bbox[2]),
                                float(found_t.bbox[3]),
                            )
                            table_obj = TableExtractor.to_markdown(
                                raw_table=raw_matrix,
                                table_id=tbl_id,
                                page_number=page_num,
                                bbox=tbl_bbox,
                            )
                            if table_obj:
                                extracted_tables.append(table_obj)
                                table_bboxes.append(tbl_bbox)

                    # 2. Extract narrative text outside table bboxes to prevent duplication
                    if table_bboxes:
                        outside_fn = partial(self.is_outside_tables, bboxes=tuple(table_bboxes))
                        filtered_page = page.filter(outside_fn)
                        narrative_text = filtered_page.extract_text() or ""
                    else:
                        narrative_text = page.extract_text() or ""

                    # Clean narrative text
                    cleaned_narrative = narrative_text.strip()

                    # 3. Detect section header progression
                    current_section = self._detect_section_header(
                        cleaned_narrative, current_section
                    )

                    parsed_pages.append(
                        ParsedPage(
                            page_number=page_num,
                            narrative_text=cleaned_narrative,
                            tables=extracted_tables,
                            section_header=current_section,
                        )
                    )

            return ParsedDocument(
                document_id=doc_id,
                document_name=filename,
                total_pages=len(parsed_pages),
                pages=parsed_pages,
            )

        except DocumentParsingError:
            raise
        except Exception as exc:
            raise DocumentParsingError(
                f"Failed to parse PDF document '{filename}': {exc!s}"
            ) from exc

    def parse_file(self, file_path: str | Path, document_id: str | None = None) -> ParsedDocument:
        """Reads a local PDF file from disk and parses it."""
        path = Path(file_path)
        if not path.exists():
            raise DocumentParsingError(f"File not found at path: {path.resolve()}")
        if not path.is_file():
            raise DocumentParsingError(f"Target path is not a file: {path.resolve()}")

        try:
            with open(path, "rb") as f:
                pdf_bytes = f.read()
            return self.parse_bytes(
                pdf_bytes=pdf_bytes,
                filename=path.name,
                document_id=document_id,
            )
        except DocumentParsingError:
            raise
        except Exception as exc:
            raise DocumentParsingError(f"Error reading file '{path.name}': {exc!s}") from exc
