import hashlib
import logging
from django.db import transaction
from apps.faqs.models import FAQ
from apps.knowledge_base.models import KnowledgeDocument, DocumentChunk
from apps.knowledge_base.services.chunker import TextChunker
from apps.knowledge_base.services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)

class IngestionService:
    """
    Ingestion service that coordinates text extraction, chunking, embedding generation,
    and storage of searchable chunks in PostgreSQL.
    """
    def __init__(self, chunker: TextChunker = None, embedding_service: EmbeddingService = None):
        self.chunker = chunker or TextChunker(chunk_size=600, chunk_overlap=100)
        self.embedding_service = embedding_service or EmbeddingService()

    @transaction.atomic
    def ingest_faq(self, faq: FAQ) -> int:
        """
        Ingests a single FAQ record into the vector knowledge base.
        Deletes old chunks to prevent stale entries.
        """
        # Remove any existing chunks for this FAQ
        DocumentChunk.objects.filter(faq=faq).delete()

        if not faq.is_active:
            logger.info(f"FAQ {faq.id} is inactive; skipping chunk ingestion.")
            return 0

        keywords_str = ", ".join(faq.keywords) if isinstance(faq.keywords, list) else str(faq.keywords)
        formatted_text = (
            f"Question: {faq.question}\n"
            f"Category: {faq.category}\n"
            f"Keywords: {keywords_str}\n"
            f"Answer: {faq.answer}"
        )

        metadata = {
            'faq_id': faq.id,
            'question': faq.question,
            'category': faq.category,
            'keywords': faq.keywords,
            'source': 'faq'
        }

        chunks_data = self.chunker.split_text(formatted_text, metadata=metadata)
        if not chunks_data:
            return 0

        texts = [c['text'] for c in chunks_data]
        embeddings = self.embedding_service.get_embeddings_batch(texts)

        chunk_objs = []
        for c, emb in zip(chunks_data, embeddings):
            chunk_objs.append(
                DocumentChunk(
                    faq=faq,
                    chunk_text=c['text'],
                    chunk_index=c['index'],
                    source_metadata=c['metadata'],
                    embedding=emb
                )
            )

        DocumentChunk.objects.bulk_create(chunk_objs)
        logger.info(f"Ingested FAQ {faq.id} into {len(chunk_objs)} chunks.")
        return len(chunk_objs)

    def ingest_all_active_faqs(self) -> int:
        """
        Ingests all active FAQ records in the database.
        """
        total = 0
        for faq in FAQ.objects.filter(is_active=True):
            total += self.ingest_faq(faq)
        return total

    @transaction.atomic
    def ingest_document_text(self, document: KnowledgeDocument, text: str) -> int:
        """
        Ingests text for a KnowledgeDocument, skipping if content hash has not changed.
        """
        if not text or not text.strip():
            document.processing_status = KnowledgeDocument.STATUS_FAILED
            document.processing_error = "Document content is empty."
            document.save()
            return 0

        content_hash = hashlib.sha256(text.strip().encode('utf-8')).hexdigest()

        # If already completed with identical hash, skip redundant processing
        if (
            document.processing_status == KnowledgeDocument.STATUS_COMPLETED
            and document.content_hash == content_hash
            and document.chunks.exists()
        ):
            logger.info(f"Document {document.id} content unchanged; skipping re-ingestion.")
            return document.chunks.count()

        document.processing_status = KnowledgeDocument.STATUS_PROCESSING
        document.processing_error = None
        document.save()

        try:
            # Delete stale chunks
            DocumentChunk.objects.filter(document=document).delete()

            metadata = {
                'document_id': document.id,
                'title': document.title,
                'source_type': document.source_type,
                'source': 'document'
            }

            chunks_data = self.chunker.split_text(text, metadata=metadata)
            if not chunks_data:
                raise ValueError("No valid text chunks could be produced from document.")

            texts = [c['text'] for c in chunks_data]
            embeddings = self.embedding_service.get_embeddings_batch(texts)

            chunk_objs = []
            for c, emb in zip(chunks_data, embeddings):
                chunk_objs.append(
                    DocumentChunk(
                        document=document,
                        chunk_text=c['text'],
                        chunk_index=c['index'],
                        source_metadata=c['metadata'],
                        embedding=emb
                    )
                )

            DocumentChunk.objects.bulk_create(chunk_objs)

            document.content_hash = content_hash
            document.total_chunks = len(chunk_objs)
            document.processing_status = KnowledgeDocument.STATUS_COMPLETED
            document.save()
            return len(chunk_objs)

        except Exception as e:
            logger.error(f"Failed to ingest document {document.id}: {e}", exc_info=True)
            document.processing_status = KnowledgeDocument.STATUS_FAILED
            document.processing_error = str(e)
            document.save()
            raise
