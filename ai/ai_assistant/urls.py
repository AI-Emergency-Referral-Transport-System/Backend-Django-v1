from django.urls import path
from . import views
from .ai_views import (
    AIChatView, AIHealthView, AIStatusView, ProcessEmergencyView,
    GenerateTextView, RAGSearchView, VoiceTextView
)
urlpatterns = [
    path('chat/', AIChatView.as_view(), name='ai-chat'),
    path('chat/enhanced/', views.EnhancedAIChatView.as_view(), name='ai-chat-enhanced'),
    path('chat/quick-info/', views.AIQuickInfoView.as_view(), name='ai-quick-info'),
    path('process-emergency/', ProcessEmergencyView.as_view(), name='ai-process-emergency'),
    path('process-emergency/enhanced/', views.EnhancedEmergencyProcessView.as_view(), name='ai-process-emergency-enhanced'),
    path('process-emergency/comprehensive/', views.AIComprehensiveEmergencyView.as_view(), name='ai-process-emergency-comprehensive'),
    path('quick-emergency/', views.AIQuickEmergencyView.as_view(), name='ai-quick-emergency'),
    path('dispatch/', views.AIEmergencyDispatchView.as_view(), name='ai-dispatch'),
    path('languages/', views.AISupportedLanguagesView.as_view(), name='ai-languages'),
    path('guidelines/', views.AISafetyGuidelinesView.as_view(), name='ai-guidelines'),
    path('health/', AIHealthView.as_view(), name='ai-health'),
    path('health/comprehensive/', views.AIHealthCheckView.as_view(), name='ai-health-comprehensive'),
    path('translate/', views.AITranslateView.as_view(), name='ai-translate'),
    path('symptom-checker/', views.AISymptomCheckerView.as_view(), name='ai-symptom-checker'),
    path('status/', AIStatusView.as_view(), name='ai-status'),
    path('generate/', GenerateTextView.as_view(), name='ai-generate'),
    path('session/', views.ConversationSessionView.as_view(), name='ai-session'),
    path('voice/', views.VoiceAIView.as_view(), name='ai-voice'),
    path('voice/text/', VoiceTextView.as_view(), name='ai-voice-text'),
    path('train/', views.AITrainView.as_view(), name='ai-train'),
    path('messages/', views.AIMessageListView.as_view(), name='ai-messages-list'),
    path('messages/create/', views.AIMessageCreateView.as_view(), name='ai-messages-create'),
    path('rag/search/', RAGSearchView.as_view(), name='ai-rag-search'),
    path('resources/nearby/', views.AINearbyResourcesView.as_view(), name='ai-resources-nearby'),
    path('resources/ambulances/', views.AIAmbulanceListView.as_view(), name='ai-ambulances'),
    path('resources/hospitals/', views.AIHospitalListView.as_view(), name='ai-hospitals'),
    path('resources/one-tap/', views.AIOneTapCallView.as_view(), name='ai-one-tap'),
    path('user/profile/', views.AIUserProfileView.as_view(), name='ai-user-profile'),
]