from rest_framework import serializers
from .models import Conversation, Message

class MessageSerializer(serializers.ModelSerializer):
    """
    Serializer for individual conversation messages.
    """
    timestamp = serializers.DateTimeField(source='created_at', read_only=True)

    class Meta:
        model = Message
        fields = [
            'id',
            'sender',
            'text',
            'sources',
            'category',
            'matched',
            'timestamp'
        ]
        read_only_fields = ['id', 'timestamp']


class ConversationSerializer(serializers.ModelSerializer):
    """
    Serializer for Conversations, including nested messages and message counts.
    """
    messages = MessageSerializer(many=True, read_only=True)
    message_count = serializers.IntegerField(source='messages.count', read_only=True)
    updatedAt = serializers.DateTimeField(source='updated_at', read_only=True)
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)

    class Meta:
        model = Conversation
        fields = [
            'id',
            'session_id',
            'title',
            'message_count',
            'createdAt',
            'updatedAt',
            'messages'
        ]
        read_only_fields = ['id', 'createdAt', 'updatedAt', 'message_count', 'messages']
