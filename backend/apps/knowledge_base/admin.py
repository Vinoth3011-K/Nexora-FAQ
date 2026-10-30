from django.contrib import admin
from .models import KnowledgeDocument, DocumentChunk

@admin.register(KnowledgeDocument)
class KnowledgeDocumentAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'source_type', 'processing_status', 'total_chunks', 'created_at')
    list_filter = ('processing_status', 'source_type', 'created_at')
    search_fields = ('title', 'processing_error')
    readonly_fields = ('content_hash', 'total_chunks', 'created_at', 'updated_at')


@admin.register(DocumentChunk)
class DocumentChunkAdmin(admin.ModelAdmin):
    list_display = ('id', 'source_display', 'chunk_index', 'preview_text', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('chunk_text',)

    def source_display(self, obj):
        if obj.faq:
            return f"FAQ #{obj.faq_id}"
        if obj.document:
            return f"Doc #{obj.document_id} ({obj.document.title})"
        return "Unknown"
    source_display.short_description = "Source"

    def preview_text(self, obj):
        return obj.chunk_text[:80] + "..." if len(obj.chunk_text) > 80 else obj.chunk_text
    preview_text.short_description = "Chunk Preview"
