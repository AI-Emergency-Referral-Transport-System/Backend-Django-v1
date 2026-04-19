import logging
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from django.conf import settings

logger = logging.getLogger(__name__)


class AIChatView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        message = request.data.get('message', '')
        user_id = request.data.get('user_id')
        language = request.data.get('language', 'en')
        
        if not message:
            return Response({'error': 'Message required'}, status=status.HTTP_400_BAD_REQUEST)
        
        from .engine import AIEngine
        engine = AIEngine()
        response = engine.process_message(message, user_id=user_id, language=language)
        
        return Response({'success': True, 'response': response})


class AIHealthView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        return Response({
            'status': 'healthy',
            'service': 'ai_assistant',
            'version': '1.0.0'
        })


class AIStatusView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        from .llm_service import LLMService
        llm = LLMService()
        return Response({
            'status': 'online',
            'providers': llm.get_available_providers(),
            'default_provider': settings.AI_PROVIDER if hasattr(settings, 'AI_PROVIDER') else 'openai'
        })


class ProcessEmergencyView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        text = request.data.get('text', '')
        language = request.data.get('language', 'en')
        
        if not text:
            return Response({'error': 'Text required'}, status=status.HTTP_400_BAD_REQUEST)
        
        from .ai_integration import emergency_analyzer
        result = emergency_analyzer.analyze_emergency_text(text, language)
        
        return Response({'success': True, **result})


class GenerateTextView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        prompt = request.data.get('prompt', '')
        language = request.data.get('language', 'en')
        context = request.data.get('context', {})
        
        if not prompt:
            return Response({'error': 'Prompt required'}, status=status.HTTP_400_BAD_REQUEST)
        
        from .engine import AIEngine
        engine = AIEngine()
        result = engine.generate_text(prompt, language=language, context=context)
        
        return Response({'success': True, 'text': result})


class RAGSearchView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        query = request.data.get('query', '')
        language = request.data.get('language', 'en')
        
        if not query:
            return Response({'error': 'Query required'}, status=status.HTTP_400_BAD_REQUEST)
        
        from .engine import AIEngine
        engine = AIEngine()
        results = engine.rag_search(query, language=language)
        
        return Response({'success': True, 'results': results})


class VoiceTextView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        audio_data = request.data.get('audio')
        language = request.data.get('language', 'en')
        
        if not audio_data:
            return Response({'error': 'Audio required'}, status=status.HTTP_400_BAD_REQUEST)
        
        from .voice import SpeechToText
        stt = SpeechToText()
        text = stt.transcribe(audio_data, language=language)
        
        return Response({'success': True, 'text': text})