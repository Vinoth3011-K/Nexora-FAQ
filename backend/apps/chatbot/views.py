import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from apps.conversations.models import Conversation, Message
from apps.chatbot.serializers import ChatRequestSerializer
from apps.chatbot.services.rag_service import RAGService

logger = logging.getLogger(__name__)


class ChatAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = ChatRequestSerializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return Response(
                {
                    'status': 'error',
                    'message': 'Invalid chat request.',
                    'errors': serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = request.user
        user_query = serializer.validated_data['query']
        conversation = serializer.validated_data.get('conversation')

        title = user_query[:36] + '...' if len(user_query) > 36 else user_query
        if not conversation:
            conversation = Conversation.objects.create(title=title, user=user)
        elif conversation.user is None:
            conversation.user = user
            conversation.save(update_fields=['user', 'updated_at'])
        elif conversation.user != user:
            conversation = Conversation.objects.create(title=title, user=user)

        user_message = Message.objects.create(
            conversation=conversation,
            sender='user',
            text=user_query,
        )

        recent_messages = (
            conversation.messages.exclude(id=user_message.id)
            .order_by('-created_at')[:8]
        )
        history = [
            {'sender': m.sender, 'text': m.text}
            for m in reversed(list(recent_messages))
        ]

        if conversation.messages.count() <= 2 and conversation.title == 'New Conversation':
            conversation.title = title
            conversation.save(update_fields=['title', 'updated_at'])

        rag_service = RAGService()
        result = rag_service.answer_question(user_query, conversation_history=history)

        answer = result.get('answer', '')
        sources = result.get('sources', [])
        matched = result.get('matched', False)

        primary_category = next((s['category'] for s in sources if s.get('category')), None)

        assistant_message = Message.objects.create(
            conversation=conversation,
            sender='assistant',
            text=answer,
            sources=sources,
            category=primary_category,
            matched=matched,
        )

        return Response(
            {
                'status': 'success',
                'answer': answer,
                'conversation_id': str(conversation.id),
                'session_id': conversation.session_id,
                'sources': sources,
                'matched': matched,
                'category': primary_category,
                'timestamp': assistant_message.created_at.isoformat(),
            },
            status=status.HTTP_200_OK,
        )
