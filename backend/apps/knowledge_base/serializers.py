from rest_framework import serializers
from django.conf import settings
from .models import KnowledgeDocument, DocumentChunk

class DocumentChunkSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentChunk
        fields = [
            'id',
            'document',
            'faq',
            'chunk_text',
            'chunk_index',
            'source_metadata',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class KnowledgeDocumentSerializer(serializers.ModelSerializer):
    chunks_count = serializers.IntegerField(source='chunks.count', read_only=True)

    class Meta:
        model = KnowledgeDocument
        fields = [
            'id',
            'title',
            'source_type',
            'file',
            'processing_status',
            'processing_error',
            'total_chunks',
            'chunks_count',
            'created_at',
            'updated_at'
        ]
        read_only_fields = [
            'id',
            'processing_status',
            'processing_error',
            'total_chunks',
            'chunks_count',
            'created_at',
            'updated_at'
        ]

    def validate_file(self, value):
        if value:
            max_size = getattr(settings, 'MAX_UPLOAD_SIZE', 5242880)
            if value.size > max_size:
                raise serializers.ValidationError(f"File size exceeds maximum allowed {max_size / (1024 * 1024):.1f}MB.")
            # Allowed extensions
            allowed_exts = ('.txt', '.md', '.json', '.csv', '.pdf')
            if not any(value.name.lower().endswith(ext) for ext in allowed_exts):
                raise serializers.ValidationError(f"Unsupported file format. Allowed: {', '.join(allowed_exts)}.")
        return value
