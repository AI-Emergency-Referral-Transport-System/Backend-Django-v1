import logging
import json
from typing import Dict, Any, Optional
from django.conf import settings

logger = logging.getLogger(__name__)


class AIEngine:
    def __init__(self):
        self.llm_service = None
        self._init_llm()
    
    def _init_llm(self):
        try:
            from .llm_service import LLMService
            self.llm_service = LLMService()
        except Exception as e:
            logger.warning(f"LLM service not available: {e}")
    
    def process_message(
        self, 
        message: str, 
        user_id: Optional[str] = None,
        language: str = 'en',
        context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        try:
            from .prompts import EMERGENCY_SYSTEM_PROMPT_EN, EMERGENCY_RESOURCE_PROMPT_EN
            from .ai_integration import emergency_analyzer, location_service
            
            message_lower = message.lower()
            is_emergency = any(
                kw in message_lower 
                for kw in ['emergency', 'urgent', 'help', 'አደጋ', 'ህመም', '911', '907']
            )
            
            if is_emergency:
                analyzed = emergency_analyzer.analyze_emergency_text(message, language)
                return self._handle_emergency(message, analyzed, language, context)
            
            return self._handle_general(message, language, context)
            
        except Exception as e:
            logger.error(f"AI process_message error: {e}")
            return {
                'response': 'Sorry, I encountered an error processing your request.',
                'error': str(e)
            }
    
    def _handle_emergency(
        self, 
        message: str, 
        analyzed: Dict, 
        language: str,
        context: Optional[Dict]
    ) -> Dict:
        emergency_type = analyzed.get('detected_type', 'other')
        priority = analyzed.get('priority', 'medium')
        
        response_data = {
            'emergency_detected': True,
            'emergency_type': emergency_type,
            'priority': priority,
            'confidence': analyzed.get('confidence', 0.5),
            'needs_immediate_dispatch': analyzed.get('needs_immediate_dispatch', False),
        }
        
        if context and context.get('latitude') and context.get('longitude'):
            lat = context['latitude']
            lon = context['longitude']
            
            from .services import AmbulanceService, HospitalService
            ambulance_svc = AmbulanceService()
            hospital_svc = HospitalService()
            
            ambulances = ambulance_svc.get_available_ambulances(lat, lon)
            hospitals = hospital_svc.get_nearby_hospitals(lat, lon)
            
            response_data['resources'] = {
                'nearest_ambulance': ambulances[0] if ambulances else None,
                'nearest_hospital': hospitals[0] if hospitals else None,
                'one_tap_call': '907',
            }
        
        if language == 'am':
            messages = {
                'critical': 'አስቸኳይ ነው! ወዲያውኑ የ907ን ይደውሉ',
                'high': 'አስቸኳይ ነው። አምቡላንስ ይጠብቡ',
                'medium': 'እንደውለን አምቡላንስ ይሰጣልዎት',
                'low': 'አምቡላንስ ይመጣልዎት'
            }
            response_data['message'] = messages.get(priority, messages['medium'])
        else:
            messages = {
                'critical': 'This is urgent! Call 907 immediately for ambulance.',
                'high': 'This is urgent. An ambulance is being dispatched.',
                'medium': 'An ambulance will be dispatched shortly.',
                'low': 'An ambulance will be assigned.'
            }
            response_data['message'] = messages.get(priority, messages['medium'])
        
        return response_data
    
    def _handle_general(
        self, 
        message: str, 
        language: str,
        context: Optional[Dict]
    ) -> Dict:
        message_lower = message.lower()
        
        if any(w in message_lower for w in ['hospital', 'ሆስፒታል', 'clinic']):
            return self._handle_hospital_search(message, language, context)
        elif any(w in message_lower for w in ['ambulance', 'አምቡላንስ']):
            return self._handle_ambulance_info(message, language, context)
        elif any(w in message_lower for w in ['one tap', 'call', '907', 'ይደውሉ']):
            return self._handle_call_info(language)
        
        return {
            'response': 'I can help you find hospitals, ambulances, or emergency services. Please provide more details.',
        }
    
    def _handle_hospital_search(
        self, 
        message: str, 
        language: str,
        context: Optional[Dict]
    ) -> Dict:
        if not context or not context.get('latitude'):
            return {
                'response': 'Please provide your location for hospital search.',
                'needs_location': True
            }
        
        from .services import HospitalService
        hospital_svc = HospitalService()
        hospitals = hospital_svc.get_nearby_hospitals(
            context['latitude'], 
            context['longitude']
        )
        
        return {
            'response': f'Found {len(hospitals)} nearby hospitals',
            'hospitals': hospitals[:5],
            'needs_location': False
        }
    
    def _handle_ambulance_info(
        self, 
        message: str, 
        language: str,
        context: Optional[Dict]
    ) -> Dict:
        if language == 'am':
            return {
                'response': '907ን ይደውሉ ለአምቡላንስ ድንገት የአሜሪካስ አገልግሎት',
                'one_tap': {'number': '907'}
            }
        return {
            'response': 'Call 907 for ambulance dispatch.',
            'one_tap': {'number': '907'}
        }
    
    def _handle_call_info(self, language: str) -> Dict:
        if language == 'am':
            return {
                'response': '907 ለአምቡላንስ',
                'numbers': {
                    'ambulance': '907',
                    'police': '991',
                    'fire': '939'
                }
            }
        return {
            'response': 'Call 907 for ambulance',
            'numbers': {
                'ambulance': '907',
                'police': '991',
                'fire': '939'
            }
        }
    
    def generate_text(
        self, 
        prompt: str, 
        language: str = 'en',
        context: Optional[Dict] = None
    ) -> str:
        if not self.llm_service:
            return "AI service is not available."
        
        try:
            return self.llm_service.generate(prompt, context or {})
        except Exception as e:
            logger.error(f"Generate text error: {e}")
            return "Sorry, I could not generate a response."
    
    def rag_search(
        self, 
        query: str, 
        language: str = 'en'
    ) -> list:
        return []


ai_engine = AIEngine()