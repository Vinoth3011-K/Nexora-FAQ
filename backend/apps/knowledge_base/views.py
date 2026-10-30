import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from .models import KnowledgeDocument
from .serializers import KnowledgeDocumentSerializer, DocumentChunkSerializer
from .services.ingestion_service import IngestionService

logger = logging.getLogger(__name__)

class KnowledgeDocumentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Knowledge Documents and their processed vector chunks.
    Read-only for public, modifications restricted to authenticated users/admins.
    """
    queryset = KnowledgeDocument.objects.all().order_by('-created_at')
    serializer_class = KnowledgeDocumentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        doc = serializer.save()
        # If text content or file is present, trigger ingestion
        raw_text = self.request.data.get('text', '')
        if not raw_text and doc.file:
            try:
                doc.file.seek(0)
                raw_text = doc.file.read().decode('utf-8', errors='ignore')
            except Exception as e:
                logger.error(f"Error reading file for document {doc.id}: {e}")
                doc.processing_status = KnowledgeDocument.STATUS_FAILED
                doc.processing_error = f"Failed to read file content: {str(e)}"
                doc.save()
                return

        if raw_text:
            try:
                ingestion_service = IngestionService()
                ingestion_service.ingest_document_text(doc, raw_text)
            except Exception as e:
                logger.error(f"Ingestion failed for doc {doc.id}: {e}")

    @action(detail=True, methods=['post'], url_path='reprocess')
    def reprocess(self, request, pk=None):
        """
        Reprocess an existing document, clearing stale chunks and generating fresh embeddings.
        """
        doc = self.get_object()
        raw_text = request.data.get('text', '')
        if not raw_text and doc.file:
            try:
                doc.file.seek(0)
                raw_text = doc.file.read().decode('utf-8', errors='ignore')
            except Exception as e:
                return Response(
                    {'status': 'error', 'message': f"Cannot read file: {str(e)}"},
                    status=status.HTTP_400_BAD_REQUEST
                )

        if not raw_text:
            return Response(
                {'status': 'error', 'message': "No content provided to reprocess."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Force re-ingestion by clearing hash
            doc.content_hash = ""
            ingestion_service = IngestionService()
            chunks_count = ingestion_service.ingest_document_text(doc, raw_text)
            serializer = self.get_serializer(doc)
            return Response({
                'status': 'success',
                'message': f"Successfully reprocessed document into {chunks_count} chunks.",
                'document': serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {'status': 'error', 'message': f"Reprocessing failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'], url_path='chunks')
    def chunks(self, request, pk=None):
        """
        List chunks generated for this specific document.
        """
        doc = self.get_object()
        chunks = doc.chunks.all().order_by('chunk_index')
        page = self.paginate_queryset(chunks)
        if page is not None:
            serializer = DocumentChunkSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = DocumentChunkSerializer(chunks, many=True)
        return Response(serializer.data)
