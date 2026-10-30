from django.core.management.base import BaseCommand
from apps.knowledge_base.services.ingestion_service import IngestionService
from apps.knowledge_base.models import DocumentChunk, KnowledgeDocument
from apps.faqs.models import FAQ

class Command(BaseCommand):
    help = 'Re-embeds all active FAQs and documents using the configured embedding provider.'

    def handle(self, *args, **options):
        self.stdout.write("Starting re-embedding process with real SentenceTransformer embeddings...")
        
        # Clear legacy incompatible chunks if needed
        ingestion = IngestionService()
        total_faqs = FAQ.objects.filter(is_active=True).count()
        self.stdout.write(f"Found {total_faqs} active FAQs to embed.")
        
        reembedded_chunks = ingestion.ingest_all_active_faqs()
        self.stdout.write(self.style.SUCCESS(f"Successfully re-embedded {reembedded_chunks} chunks for {total_faqs} FAQs."))
        
        # Also re-embed any completed documents if present
        docs = KnowledgeDocument.objects.filter(processing_status=KnowledgeDocument.STATUS_COMPLETED)
        if docs.exists():
            for doc in docs:
                if doc.file:
                    try:
                        content = doc.file.read().decode('utf-8')
                        ingestion.ingest_document_text(doc, content)
                        self.stdout.write(f"Re-embedded document: {doc.title}")
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f"Failed to re-embed doc {doc.id}: {e}"))

        # Verify dimension
        sample_chunk = DocumentChunk.objects.first()
        if sample_chunk and isinstance(sample_chunk.embedding, list):
            dim = len(sample_chunk.embedding)
            self.stdout.write(self.style.SUCCESS(f"Verification: Chunks now have embedding dimension {dim}."))
