"""
Vector storage adapter using Qdrant (in-memory or cloud cluster).
Provides dense vector similarity search with metadata filtering for ApexFin AI.
"""

import uuid
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.http import models as rest_models

from src.config.settings import get_settings
from src.domain.entities import ChunkMetadata, DocumentChunk


class QdrantVectorStore:
    """
    Manages collection lifecycle, chunk indexing, and cosine similarity search
    in Qdrant vector database.
    """

    def __init__(
        self,
        url: str | None = None,
        api_key: str | None = None,
        collection_name: str | None = None,
        client: QdrantClient | None = None,
    ):
        settings = get_settings()
        self.url = url or settings.QDRANT_URL
        self.api_key = api_key or settings.QDRANT_API_KEY
        self.collection_name = collection_name or settings.QDRANT_COLLECTION_NAME

        if client is not None:
            self.client = client
        elif self.url == ":memory:":
            self.client = QdrantClient(location=":memory:")
        else:
            self.client = QdrantClient(url=self.url, api_key=self.api_key)

    def ensure_collection(
        self,
        vector_size: int = 384,
        distance: rest_models.Distance = rest_models.Distance.COSINE,
    ) -> None:
        """Creates collection if it does not already exist."""
        collections_response = self.client.get_collections()
        existing_names = [col.name for col in collections_response.collections]

        if self.collection_name not in existing_names:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=rest_models.VectorParams(
                    size=vector_size,
                    distance=distance,
                ),
            )

    def upsert_chunks(
        self,
        chunks: list[DocumentChunk],
        embeddings: list[list[float]],
    ) -> None:
        """Stores a batch of DocumentChunks along with their dense embedding vectors."""
        if not chunks or not embeddings:
            return

        if len(chunks) != len(embeddings):
            raise ValueError(
                f"Mismatch: received {len(chunks)} chunks and {len(embeddings)} embeddings."
            )

        self.ensure_collection(vector_size=len(embeddings[0]))

        points: list[rest_models.PointStruct] = []
        for chunk, emb in zip(chunks, embeddings, strict=True):
            # Ensure valid UUID for Qdrant point ID
            try:
                point_id = str(uuid.UUID(chunk.chunk_id))
            except ValueError:
                point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, chunk.chunk_id))

            payload: dict[str, Any] = {
                "chunk_id": chunk.chunk_id,
                "content": chunk.content,
                "document_id": chunk.metadata.document_id,
                "document_name": chunk.metadata.document_name,
                "page_number": chunk.metadata.page_number,
                "chunk_index": chunk.metadata.chunk_index,
                "is_table": chunk.metadata.is_table,
                "table_id": chunk.metadata.table_id,
                "section_header": chunk.metadata.section_header,
            }

            points.append(
                rest_models.PointStruct(
                    id=point_id,
                    vector=emb,
                    payload=payload,
                )
            )

        self.client.upsert(
            collection_name=self.collection_name,
            points=points,
            wait=True,
        )

    def search(
        self,
        query_vector: list[float],
        limit: int = 25,
        document_id: str | None = None,
    ) -> list[DocumentChunk]:
        """Performs cosine vector search, returning top-k matching DocumentChunks."""
        query_filter: rest_models.Filter | None = None
        if document_id:
            query_filter = rest_models.Filter(
                must=[
                    rest_models.FieldCondition(
                        key="document_id",
                        match=rest_models.MatchValue(value=document_id),
                    )
                ]
            )

        # Call search on Qdrant
        search_results = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            query_filter=query_filter,
            limit=limit,
            with_payload=True,
        ).points

        matched_chunks: list[DocumentChunk] = []
        for scored_point in search_results:
            payload = scored_point.payload or {}
            meta = ChunkMetadata(
                document_id=payload.get("document_id", ""),
                document_name=payload.get("document_name", ""),
                page_number=payload.get("page_number", 1),
                chunk_index=payload.get("chunk_index", 0),
                is_table=payload.get("is_table", False),
                table_id=payload.get("table_id"),
                section_header=payload.get("section_header"),
            )
            chunk = DocumentChunk(
                chunk_id=payload.get("chunk_id", str(scored_point.id)),
                content=payload.get("content", ""),
                metadata=meta,
                dense_score=float(scored_point.score),
            )
            matched_chunks.append(chunk)

        return matched_chunks

    def delete_document(self, document_id: str) -> None:
        """Deletes all indexed chunks associated with a specific document ID."""
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=rest_models.FilterSelector(
                filter=rest_models.Filter(
                    must=[
                        rest_models.FieldCondition(
                            key="document_id",
                            match=rest_models.MatchValue(value=document_id),
                        )
                    ]
                )
            ),
            wait=True,
        )

    def count(self, document_id: str | None = None) -> int:
        """Returns total chunk count in collection, optionally filtered by document."""
        count_filter: rest_models.Filter | None = None
        if document_id:
            count_filter = rest_models.Filter(
                must=[
                    rest_models.FieldCondition(
                        key="document_id",
                        match=rest_models.MatchValue(value=document_id),
                    )
                ]
            )
        response = self.client.count(
            collection_name=self.collection_name,
            count_filter=count_filter,
            exact=True,
        )
        return response.count

    def list_documents(self) -> list[dict[str, Any]]:
        """Returns metadata summary for all distinct indexed documents."""
        try:
            records, _ = self.client.scroll(
                collection_name=self.collection_name,
                limit=500,
                with_payload=True,
                with_vectors=False,
            )
            docs: dict[str, dict[str, Any]] = {}
            for point in records:
                payload = point.payload or {}
                d_id = payload.get("document_id")
                d_name = payload.get("document_name")
                if d_id and d_name:
                    if d_id not in docs:
                        docs[d_id] = {
                            "document_id": d_id,
                            "document_name": d_name,
                            "total_pages": payload.get("page_number", 1),
                            "total_chunks": 1,
                        }
                    else:
                        docs[d_id]["total_chunks"] += 1
                        docs[d_id]["total_pages"] = max(
                            docs[d_id]["total_pages"], payload.get("page_number", 1)
                        )
            return list(docs.values())
        except Exception:
            return []

    def get_all_chunks(self) -> list[DocumentChunk]:
        """
        Scrolls and reconstructs all DocumentChunks currently stored in collection.
        Used to hydrate the sparse in-memory BM25 index during startup.
        """
        try:
            records, _ = self.client.scroll(
                collection_name=self.collection_name,
                limit=10000,
                with_payload=True,
                with_vectors=False,
            )
            chunks: list[DocumentChunk] = []
            for point in records:
                payload = point.payload or {}
                meta = ChunkMetadata(
                    document_id=payload.get("document_id", ""),
                    document_name=payload.get("document_name", ""),
                    page_number=payload.get("page_number", 1),
                    chunk_index=payload.get("chunk_index", 0),
                    is_table=payload.get("is_table", False),
                    table_id=payload.get("table_id"),
                    section_header=payload.get("section_header"),
                )
                chunk = DocumentChunk(
                    chunk_id=payload.get("chunk_id", str(point.id)),
                    content=payload.get("content", ""),
                    metadata=meta,
                )
                chunks.append(chunk)
            return chunks
        except Exception:
            return []
