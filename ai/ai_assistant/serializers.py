
from rest_framework import serializers
from ...accounts.models import AIMessage, AIConversationSession
class AIMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIMessage
        fields = [
            'id', 'emergency', 'user', 'sender', 'message',
            'voice_url', 'language', 'intent', 'metadata', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
class AIMessageCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIMessage
        fields = ['message', 'voice_url', 'language', 'emergency']
class AIConversationSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIConversationSession
        fields = [
            'id', 'session_id', 'language', 'is_active',
            'message_count', 'last_message_at', 'created_at'
        ]
        read_only_fields = ['id', 'session_id', 'created_at']
