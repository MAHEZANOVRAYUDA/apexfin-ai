"""
Hierarchical context-aware chunker for financial documents.
Preserves financial tables as atomic units and segments narrative text with sliding token overlap.
"""

import re
import uuid

from src.domain.entities import ChunkMetadata, DocumentChunk
from src.ingestion.pdf_parser import ParsedDocument


class HierarchicalChunker:
    """
    Splits ParsedDocument into an ordered list of DocumentChunk entities.
    Enforces two strict invariant rules:
    1. Financial tables are NEVER split across chunks (Atomic Table Preservation).
    2. Narrative text respects paragraph and sentence boundaries with configurable overlap.
    """

    def __init__(
        self,
        chunk_size_tokens: int = 512,
        overlap_tokens: int = 64,
        min_chunk_tokens: int = 25,
    ):
        # 1 token is approximately 0.75 words, so words = tokens * 0.75
        self.chunk_size_words = max(int(chunk_size_tokens * 0.75), 50)
        self.overlap_words = max(int(overlap_tokens * 0.75), 10)
        self.min_chunk_words = max(int(min_chunk_tokens * 0.75), 5)

    def _split_into_sentences(self, text: str) -> list[str]:
        """Splits narrative text into clean sentence segments."""
        # Split on sentence ending punctuation followed by space or newline
        sentences = re.split(r"(?<=[.!?])\s+", text)
        return [s.strip() for s in sentences if s.strip()]

    def _chunk_narrative_text(
        self,
        text: str,
        document_id: str,
        document_name: str,
        page_number: int,
        section_header: str | None,
        start_chunk_idx: int,
    ) -> list[DocumentChunk]:
        """Chunks page narrative into overlapping windows while respecting sentence boundaries."""
        sentences = self._split_into_sentences(text)
        if not sentences:
            return []

        chunks: list[DocumentChunk] = []
        current_words: list[str] = []
        current_chunk_idx = start_chunk_idx

        for sentence in sentences:
            sentence_words = sentence.split()
            if not sentence_words:
                continue

            # If adding this sentence exceeds chunk size and we already have sufficient content
            if len(current_words) + len(sentence_words) > self.chunk_size_words and current_words:
                chunk_text = " ".join(current_words)
                chunks.append(
                    DocumentChunk(
                        chunk_id=str(uuid.uuid4()),
                        content=chunk_text,
                        metadata=ChunkMetadata(
                            document_id=document_id,
                            document_name=document_name,
                            page_number=page_number,
                            chunk_index=current_chunk_idx,
                            is_table=False,
                            table_id=None,
                            section_header=section_header,
                        ),
                    )
                )
                current_chunk_idx += 1

                # Carry over overlap words from tail of previous buffer
                if len(current_words) > self.overlap_words:
                    current_words = current_words[-self.overlap_words :]
                current_words.extend(sentence_words)
            else:
                current_words.extend(sentence_words)

        # Flush any remaining words if they meet the minimum threshold or if no chunks were created yet
        if current_words and (len(current_words) >= self.min_chunk_words or not chunks):
            chunk_text = " ".join(current_words)
            chunks.append(
                DocumentChunk(
                    chunk_id=str(uuid.uuid4()),
                    content=chunk_text,
                    metadata=ChunkMetadata(
                        document_id=document_id,
                        document_name=document_name,
                        page_number=page_number,
                        chunk_index=current_chunk_idx,
                        is_table=False,
                        table_id=None,
                        section_header=section_header,
                    ),
                )
            )

        return chunks

    def chunk_document(self, doc: ParsedDocument) -> list[DocumentChunk]:
        """
        Processes entire ParsedDocument into sequenced DocumentChunks.
        Yields table chunks first, followed by narrative chunks per page.
        """
        all_chunks: list[DocumentChunk] = []
        global_chunk_idx = 0

        for page in doc.pages:
            # 1. Preserved Atomic Tables
            for table in page.tables:
                table_chunk = DocumentChunk(
                    chunk_id=str(uuid.uuid4()),
                    content=table.markdown,
                    metadata=ChunkMetadata(
                        document_id=doc.document_id,
                        document_name=doc.document_name,
                        page_number=page.page_number,
                        chunk_index=global_chunk_idx,
                        is_table=True,
                        table_id=table.table_id,
                        section_header=page.section_header,
                    ),
                )
                all_chunks.append(table_chunk)
                global_chunk_idx += 1

            # 2. Segmented Narrative Text
            if page.narrative_text:
                narrative_chunks = self._chunk_narrative_text(
                    text=page.narrative_text,
                    document_id=doc.document_id,
                    document_name=doc.document_name,
                    page_number=page.page_number,
                    section_header=page.section_header,
                    start_chunk_idx=global_chunk_idx,
                )
                all_chunks.extend(narrative_chunks)
                global_chunk_idx += len(narrative_chunks)

        return all_chunks
