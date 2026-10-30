from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import Conversation
from .serializers import ConversationSerializer


class ConversationViewSet(viewsets.ModelViewSet):
    serializer_class = ConversationSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'

    def get_queryset(self):
        user = self.request.user
        if not user or not user.is_authenticated:
            return Conversation.objects.none()

        queryset = Conversation.objects.filter(user=user).prefetch_related('messages')
        session_id = self.request.query_params.get('session_id')
        if session_id:
            queryset = queryset.filter(session_id=session_id)

        return queryset.filter(messages__isnull=False).distinct().order_by('-updated_at')

    def create(self, request, *args, **kwargs):
        title = request.data.get('title', 'New Conversation')
        session_id = request.data.get('session_id', '')

        conversation = Conversation.objects.create(
            user=request.user,
            title=title.strip() if title else 'New Conversation',
            session_id=session_id.strip() if session_id else '',
        )
        serializer = self.get_serializer(conversation)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='clear')
    def clear(self, request, id=None):
        conversation = self.get_object()
        conversation.messages.all().delete()
        conversation.title = 'New Conversation'
        conversation.save()
        serializer = self.get_serializer(conversation)
        return Response({
            'status': 'success',
            'message': 'Conversation cleared successfully.',
            'conversation': serializer.data,
        }, status=status.HTTP_200_OK)
