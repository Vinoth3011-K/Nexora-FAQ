from django.db import models
from django.conf import settings
from apps.faqs.models import FAQ

# Dynamic Vector Field handling: If USE_PGVECTOR is active and pgvector installed, use VectorField; otherwise JSONField
def get_embedding_field():
    if getattr(settings, 'USE_PGVECTOR', False):
        try:
            from pgvector.django import VectorField
            return VectorField(dimensions=getattr(settings, 'EMBEDDING_DIMENSION', 384), null=True, blank=True)
        except Exception:
            pass
    return models.JSONField(default=list, blank=True, help_text="Embedding vector stored as JSON array of floats")

EmbeddingField = get_embedding_field


class KnowledgeDocument(models.Model):
    """
    Source document uploaded or imported for FAQ knowledge base ingestion.
    """
    STATUS_PENDING = 'pending'
    STATUS_PROCESSING = 'processing'
    STATUS_COMPLETED = 'completed'
    STATUS_FAILED = 'failed'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_PROCESSING, 'Processing'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_FAILED, 'Failed'),
    ]

    title = models.CharField(max_length=255)
    source_type = models.CharField(max_length=50, default='text')
    file = models.FileField(upload_to='documents/', null=True, blank=True)
    content_hash = models.CharField(max_length=64, blank=True, db_index=True)
    processing_status = models.CharField(
        max_length=30, 
        choices=STATUS_CHOICES, 
        default=STATUS_PENDING,
        db_index=True
    )
    processing_error = models.TextField(blank=True, null=True)
    total_chunks = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Knowledge Document"
        verbose_name_plural = "Knowledge Documents"

    def __str__(self):
        return f"{self.title} ({self.processing_status})"


class DocumentChunk(models.Model):
    """
    Searchable chunk extracted from a KnowledgeDocument or directly from an FAQ.
    """
    document = models.ForeignKey(
        KnowledgeDocument, 
        on_delete=models.CASCADE, 
        related_name='chunks',
        null=True, 
        blank=True
    )
    faq = models.ForeignKey(
        FAQ, 
        on_delete=models.CASCADE, 
        related_name='chunks',
        null=True, 
        blank=True
    )
    chunk_text = models.TextField()
    chunk_index = models.PositiveIntegerField(default=0)
    source_metadata = models.JSONField(default=dict, blank=True)
    embedding = EmbeddingField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['document', 'chunk_index']
        indexes = [
            models.Index(fields=['faq']),
            models.Index(fields=['document', 'chunk_index']),
        ]
        verbose_name = "Document Chunk"
        verbose_name_plural = "Document Chunks"

    def __str__(self):
        source = f"FAQ {self.faq_id}" if self.faq_id else f"Doc {self.document_id}"
        return f"Chunk #{self.chunk_index} from {source} ({len(self.chunk_text)} chars)"
