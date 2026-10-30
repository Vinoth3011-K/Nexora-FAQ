import uuid
from django.db import models
from django.conf import settings

class Conversation(models.Model):
    """
    Stores conversation sessions for server-side persistence.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='conversations',
        null=True,
        blank=True,
        db_index=True
    )
    session_id = models.CharField(max_length=120, blank=True, db_index=True)
    title = models.CharField(max_length=255, default='New Conversation')
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        verbose_name = "Conversation"
        verbose_name_plural = "Conversations"

    def __str__(self):
        return f"{self.title} ({str(self.id)[:8]})"


class Message(models.Model):
    """
    Individual user or assistant message belonging to a Conversation.
    """
    ROLE_CHOICES = [
        ('user', 'User'),
        ('assistant', 'Assistant'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(
        Conversation, 
        on_delete=models.CASCADE, 
        related_name='messages'
    )
    sender = models.CharField(max_length=20, choices=ROLE_CHOICES)
    text = models.TextField()
    sources = models.JSONField(default=list, blank=True)
    category = models.CharField(max_length=120, blank=True, null=True)
    matched = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['conversation', 'created_at']),
        ]
        verbose_name = "Message"
        verbose_name_plural = "Messages"

    def __str__(self):
        return f"[{self.sender}] {self.text[:40]}"
