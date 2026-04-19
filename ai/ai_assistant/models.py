from django.db import models
from django.conf import settings
from accounts.models import User


class AIMessage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ai_messages')
    sender = models.CharField(max_length=20, choices=[('user', 'User'), ('ai', 'AI')])
    message = models.TextField()
    language = models.CharField(max_length=10, default='en')
    emergency = models.BooleanField(default=False)
    voice_url = models.URLField(blank=True, null=True)
    intent = models.CharField(max_length=100, blank=True, null=True)
    metadata = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['emergency', '-created_at']),
        ]


class AIConversationSession(models.Model):
    session_id = models.CharField(max_length=100, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ai_sessions')
    language = models.CharField(max_length=10, default='en')
    is_active = models.BooleanField(default=True)
    message_count = models.IntegerField(default=0)
    last_message_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-last_message_at']
        indexes = [
            models.Index(fields=['user', '-last_message_at']),
            models.Index(fields=['is_active', '-last_message_at']),
        ]