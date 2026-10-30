import uuid
from rest_framework import serializers
from apps.conversations.models import Conversation

class ChatRequestSerializer(serializers.Serializer):
    """
    Serializer validating incoming chat requests.
    Supports both 'question' and 'message' fields for maximum compatibility.
    """
    question = serializers.CharField(required=False, max_length=2000, allow_blank=False)
    message = serializers.CharField(required=False, max_length=2000, allow_blank=False)
    conversation_id = serializers.CharField(required=False, allow_null=True, allow_blank=True)

    def validate(self, data):
        query = data.get('question') or data.get('message')
        if not query or not query.strip():
            raise serializers.ValidationError({"question": "Either 'question' or 'message' field is required and cannot be empty."})
        
        data['query'] = query.strip()

        conv_id = data.get('conversation_id')
        request = self.context.get('request') if hasattr(self, 'context') else None
        user = request.user if request and hasattr(request, 'user') and request.user.is_authenticated else None

        if conv_id and str(conv_id).strip() and str(conv_id).strip().lower() not in ('null', 'undefined', 'none', ''):
            cid_str = str(conv_id).strip()
            try:
                # Try validating as standard UUID
                valid_uuid = uuid.UUID(cid_str)
                if user:
                    conv = Conversation.objects.filter(id=valid_uuid, user=user).first()
                    if not conv:
                        # Fallback for legacy conversations not yet associated with a user
                        conv = Conversation.objects.filter(id=valid_uuid, user__isnull=True).first()
                else:
                    conv = Conversation.objects.filter(id=valid_uuid).first()
                data['conversation'] = conv
            except (ValueError, TypeError):
                # Map non-UUID string IDs (like client-generated conv_xxx) to session_id
                if user:
                    conv = Conversation.objects.filter(session_id=cid_str, user=user).first()
                else:
                    conv = Conversation.objects.filter(session_id=cid_str).first()
                data['conversation'] = conv
        else:
            data['conversation'] = None

        return data
