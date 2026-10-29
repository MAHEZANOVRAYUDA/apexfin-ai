"""
Unit tests for FinancialPromptBuilder, XML context segregation, and canary nonces.
"""

from src.domain.entities import ChunkMetadata, DocumentChunk
from src.generation.prompts import FinancialPromptBuilder


def test_prompt_builder_canary_injection():
    """Verify canary token is embedded into system prompt."""
    builder = FinancialPromptBuilder(canary_secret="test-secret-canary-999")
    sys_prompt = builder.build_system_prompt()

    assert "test-secret-canary-999" in sys_prompt
    assert "<!-- audit-canary: test-secret-canary-999 -->" in sys_prompt
    assert "Zero Hallucination" in sys_prompt


def test_prompt_builder_xml_evidence_formatting():
    """Verify document chunks are wrapped in XML tags with CDATA protection."""
    builder = FinancialPromptBuilder()
    meta = ChunkMetadata(
        document_id="doc-1",
        document_name="apple_10k.pdf",
        page_number=14,
        chunk_index=0,
        is_table=True,
        table_id="tbl-01",
    )
    chunk = DocumentChunk(
        chunk_id="chunk-1",
        content="| Net Sales | $383,285 |\n| Gross Margin | 44.1% |",
        metadata=meta,
    )

    evidence_xml = builder.format_retrieved_evidence([chunk])
    assert "<retrieved_evidence>" in evidence_xml
    assert "</retrieved_evidence>" in evidence_xml
    assert (
        '<chunk index="1" doc="apple_10k.pdf" page="14" is_table="true" table_id="tbl-01">'
        in evidence_xml
    )
    assert "<![CDATA[" in evidence_xml
    assert "$383,285" in evidence_xml


def test_prompt_builder_user_prompt():
    """Verify user prompt segregates query and evidence."""
    builder = FinancialPromptBuilder()
    meta = ChunkMetadata(
        document_id="doc-1",
        document_name="doc.pdf",
        page_number=1,
        chunk_index=0,
    )
    chunk = DocumentChunk(content="Operating income was $114B.", metadata=meta)

    user_msg = builder.build_user_prompt(
        query="What was operating income?",
        chunks=[chunk],
    )
    assert "<user_query>\nWhat was operating income?\n</user_query>" in user_msg
    assert "<retrieved_evidence>" in user_msg
    assert "Operating income was $114B." in user_msg
