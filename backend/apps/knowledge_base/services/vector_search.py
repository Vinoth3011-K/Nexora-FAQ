import math
from typing import List, Dict, Any
from django.conf import settings
from apps.knowledge_base.models import DocumentChunk
from apps.knowledge_base.services.embedding_service import EmbeddingService

def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """
    Computes cosine similarity between two numeric vectors.
    Returns float in range [-1.0, 1.0], typically [0.0, 1.0] for embeddings.
    """
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0

    dot_product = sum(a * b for a, b in zip(v1, v2))
    norm_a = math.sqrt(sum(a * a for a in v1))
    norm_b = math.sqrt(sum(b * b for b in v2))

    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0

    return max(0.0, min(1.0, dot_product / (norm_a * norm_b)))


class VectorSearchService:
    """
    Vector similarity search service.
    Retrieves the most semantically relevant document chunks for a query.
    """
    def __init__(self, embedding_service: EmbeddingService = None):
        self.embedding_service = embedding_service or EmbeddingService()
        self.top_k = int(getattr(settings, 'RAG_TOP_K', 4))
        self.similarity_threshold = float(getattr(settings, 'RAG_SIMILARITY_THRESHOLD', 0.25))
        self.use_pgvector = getattr(settings, 'USE_PGVECTOR', False)

    def search(self, query: str, top_k: int = None, threshold: float = None) -> List[Dict[str, Any]]:
        """
        Executes vector search for the provided query text.
        """
        if not query or not query.strip():
            return []

        k = top_k if top_k is not None else self.top_k
        min_threshold = threshold if threshold is not None else self.similarity_threshold

        query_embedding = self.embedding_service.get_embedding(query.strip())
        return self.search_by_vector(query_embedding, top_k=k, threshold=min_threshold)

    def search_by_vector(self, query_vector: List[float], top_k: int = 4, threshold: float = 0.25) -> List[Dict[str, Any]]:
        """
        Performs vector similarity search against stored DocumentChunk objects.
        """
        # If pgvector is enabled and configured in PostgreSQL
        if self.use_pgvector:
            try:
                from pgvector.django import CosineDistance
                chunks = DocumentChunk.objects.filter(embedding__isnull=False).annotate(
                    distance=CosineDistance('embedding', query_vector)
                ).order_by('distance')[:top_k]

                results = []
                for chunk in chunks:
                    similarity = 1.0 - (chunk.distance if chunk.distance is not None else 1.0)
                    if similarity >= threshold:
                        results.append(self._format_chunk_result(chunk, similarity))
                return results
            except Exception:
                # Fallback to standard Python vector search if pgvector extension fails at runtime
                pass

        # Standard PostgreSQL storage vector similarity computation
        chunks = DocumentChunk.objects.filter(embedding__isnull=False).select_related('faq', 'document')
        scored_chunks = []

        for chunk in chunks:
            chunk_vec = chunk.embedding
            if isinstance(chunk_vec, list) and len(chunk_vec) > 0:
                sim = cosine_similarity(query_vector, chunk_vec)
                if sim >= threshold:
                    scored_chunks.append((sim, chunk))

        # Sort descending by similarity score
        scored_chunks.sort(key=lambda x: x[0], reverse=True)

        results = []
        for sim, chunk in scored_chunks[:top_k]:
            results.append(self._format_chunk_result(chunk, sim))

        return results

    def _format_chunk_result(self, chunk: DocumentChunk, score: float) -> Dict[str, Any]:
        faq_id = chunk.faq_id if chunk.faq_id else None
        doc_id = chunk.document_id if chunk.document_id else None
        
        meta = chunk.source_metadata or {}
        title = meta.get('question') or meta.get('title') or (chunk.faq.question if chunk.faq else 'Document')
        category = meta.get('category') or (chunk.faq.category if chunk.faq else 'General')

        return {
            'chunk_id': chunk.id,
            'text': chunk.chunk_text,
            'faq_id': faq_id,
            'document_id': doc_id,
            'title': title,
            'category': category,
            'relevance_score': round(float(score), 4),
            'metadata': meta
        }
