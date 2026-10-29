"""
Pre-packaged SEC 10-K benchmark filings loader for ApexFin AI.
Enables immediate interactive testing of audit query templates.
"""

import logging

from src.domain.entities import ChunkMetadata, DocumentChunk
from src.retrieval.hybrid_retriever import HybridRetriever

logger = logging.getLogger(__name__)

SAMPLE_FILINGS: list[dict] = [
    {
        "document_id": "sample-apple-10k-2023",
        "document_name": "apple_10k_2023.pdf",
        "chunks": [
            {
                "chunk_id": "aapl-chunk-narrative-1",
                "page_number": 1,
                "is_table": False,
                "section": "ITEM 7. MD&A - Operations",
                "content": (
                    "ITEM 7. MANAGEMENT'S DISCUSSION AND ANALYSIS OF FINANCIAL CONDITION AND RESULTS OF OPERATIONS. "
                    "Apple Inc. fiscal year ended September 30, 2023. Total net sales were $383,285 million in 2023, "
                    "down 2.8% compared to $394,328 million in 2022. Products net sales were $298,085 million compared "
                    "to $316,199 million in 2022. Services net sales reached an all-time record of $85,200 million, "
                    "up 9.0% from $78,129 million in 2022. Research and development expense increased to $29,915 million "
                    "in 2023 from $26,251 million in 2022. Operating income was $114,301 million."
                ),
            },
            {
                "chunk_id": "aapl-chunk-table-1",
                "page_number": 1,
                "is_table": True,
                "section": "Consolidated Statements of Operations",
                "content": (
                    "### Apple Inc. Consolidated Statements of Operations (in Millions)\n"
                    "| Segment / Line Item | FY2023 | FY2022 | FY2021 |\n"
                    "| :--- | :--- | :--- | :--- |\n"
                    "| Products Net Sales | $298,085M | $316,199M | $297,392M |\n"
                    "| Services Net Sales | $85,200M | $78,129M | $68,425M |\n"
                    "| Total Net Sales | $383,285M | $394,328M | $365,817M |\n"
                    "| Research & Development | $29,915M | $26,251M | $21,914M |\n"
                    "| Operating Income | $114,301M | $119,437M | $108,949M |\n"
                    "| Net Income | $96,995M | $99,803M | $94,680M |"
                ),
            },
        ],
    },
    {
        "document_id": "sample-nvidia-10k-2024",
        "document_name": "nvidia_10k_2024.pdf",
        "chunks": [
            {
                "chunk_id": "nvda-chunk-narrative-1",
                "page_number": 1,
                "is_table": False,
                "section": "ITEM 7. MD&A - Results",
                "content": (
                    "ITEM 7. MANAGEMENT'S DISCUSSION AND ANALYSIS. NVIDIA Corporation fiscal year ended January 28, 2024. "
                    "Revenue was $60,922 million for fiscal 2024, up 126% from a year ago. Data Center revenue was $47,525 million, "
                    "up 217% driven by extraordinary enterprise demand for accelerated computing and generative AI platforms. "
                    "Gaming revenue was $10,447 million, up 15%. GAAP gross margin was 72.7% for fiscal 2024, compared to 56.9% in the prior year. "
                    "Free cash flow generation reached $27,021 million. Note 3: Long-term debt obligations totaled $8,460 million "
                    "bearing interest between 2.85% and 3.50%. Supply chain constraints in high-bandwidth memory (HBM3e) impacted early delivery timelines."
                ),
            },
            {
                "chunk_id": "nvda-chunk-table-1",
                "page_number": 1,
                "is_table": True,
                "section": "Revenue by Market Platform",
                "content": (
                    "### NVIDIA Corporation Revenue by Market Platform (in Millions)\n"
                    "| Market Platform | FY2024 | FY2023 | Change (%) |\n"
                    "| :--- | :--- | :--- | :--- |\n"
                    "| Data Center | $47,525M | $15,008M | +217% |\n"
                    "| Gaming | $10,447M | $9,067M | +15% |\n"
                    "| Professional Visualization | $1,553M | $1,544M | +1% |\n"
                    "| Automotive | $1,091M | $903M | +21% |\n"
                    "| Total Revenue | $60,922M | $26,974M | +126% |\n"
                    "| GAAP Gross Margin | 72.7% | 56.9% | +15.8 pts |\n"
                    "| Free Cash Flow | $27,021M | $3,808M | +610% |"
                ),
            },
        ],
    },
]


def load_benchmark_samples(retriever: HybridRetriever) -> int:
    """
    Indexes canonical SEC Form 10-K filings into the Hybrid Retriever.
    Returns total chunks indexed.
    """
    total_indexed = 0
    all_chunks: list[DocumentChunk] = []

    for filing in SAMPLE_FILINGS:
        doc_id = filing["document_id"]
        doc_name = filing["document_name"]

        for idx, item in enumerate(filing["chunks"]):
            chunk = DocumentChunk(
                chunk_id=item["chunk_id"],
                content=item["content"],
                metadata=ChunkMetadata(
                    document_id=doc_id,
                    document_name=doc_name,
                    page_number=item["page_number"],
                    chunk_index=idx,
                    is_table=item["is_table"],
                    section_header=item["section"],
                ),
            )
            all_chunks.append(chunk)

    if all_chunks:
        retriever.index_document_chunks(all_chunks)
        total_indexed = len(all_chunks)
        logger.info("Successfully indexed %d benchmark sample chunks.", total_indexed)

    return total_indexed
