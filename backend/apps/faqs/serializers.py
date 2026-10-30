from rest_framework import serializers
from .models import FAQ

class FAQSerializer(serializers.ModelSerializer):
    """
    Serializer for FAQ instances with full field validation.
    """
    class Meta:
        model = FAQ
        fields = [
            'id',
            'question',
            'answer',
            'category',
            'keywords',
            'is_active',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_question(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Question cannot be empty or just whitespace.")
        if len(value.strip()) < 5:
            raise serializers.ValidationError("Question must be at least 5 characters long.")
        return value.strip()

    def validate_answer(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Answer cannot be empty or just whitespace.")
        return value.strip()

    def validate_category(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Category cannot be empty.")
        return value.strip()
