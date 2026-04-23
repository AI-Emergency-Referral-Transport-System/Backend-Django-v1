import logging
import os
from typing import Dict, Any, Optional, List
from django.conf import settings

logger = logging.getLogger(__name__)


class LLMService:
    def __init__(self):
        self.provider = getattr(settings, 'AI_PROVIDER', 'openai')
        self.client = None
        self._init_client()
    
    def _init_client(self):
        try:
            if self.provider == 'openai':
                api_key = getattr(settings, 'OPENAI_API_KEY', None)
                if api_key:
                    import openai
                    openai.api_key = api_key
                    self.client = openai
            elif self.provider == 'gemini':
                api_key = getattr(settings, 'GEMINI_API_KEY', None)
                if api_key:
                    import google.generativeai as genai
                    genai.configure(api_key=api_key)
                    self.client = genai
            elif self.provider == 'ollama':
                self.client = {'url': getattr(settings, 'OLLAMA_URL', 'http://localhost:11434')}
        except Exception as e:None
        logger.warning(f"LLM client init error: {e}")
    
    def get_available_providers(self) -> List[str]:
        providers = []
        if getattr(settings, 'OPENAI_API_KEY', None):
            providers.append('openai')
        if getattr(settings, 'GEMINI_API_KEY', None):
            providers.append('gemini')
        if getattr(settings, 'OLLAMA_URL', None):
            providers.append('ollama')
        return providers
    
    def generate(
        self, 
        prompt: str, 
        context: Optional[Dict] = None,
        model: str = 'gpt-3.5-turbo'
    ) -> str:
        if not self.client:
            return self._fallback_response(prompt)
        
        try:
            if self.provider == 'openai':
                return self._generate_openai(prompt, model)
            elif self.provider == 'gemini':
                return self._generate_gemini(prompt, model)
            elif self.provider == 'ollama':
                return self._generate_ollama(prompt, model)
            return self._fallback_response(prompt)
        except Exception as e:
            logger.error(f"LLM generate error: {e}")
            return self._fallback_response(prompt)
    
    def _generate_openai(self, prompt: str, model: str) -> str:
        try:
            response = self.client.ChatCompletion.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=500
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI error: {e}")
            return self._fallback_response(prompt)
    
    def _generate_gemini(self, prompt: str, model: str = 'gemini-pro') -> str:
        try:
            model = self.client.GenerativeModel(model)
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.error(f"Gemini error: {e}")
            return self._fallback_response(prompt)
    
    def _generate_ollama(self, prompt: str, model: str = 'llama2') -> str:
        try:
            import requests
            url = f"{self.client['url']}/api/generate"
            response = requests.post(url, json={"model": model, "prompt": prompt}, timeout=30)
            if response.status_code == 200:
                return response.json().get('response', '')
            return self._fallback_response(prompt)
        except Exception as e:
            logger.error(f"Ollama error: {e}")
            return self._fallback_response(prompt)
    
    def _fallback_response(self, prompt: str) -> str:
        prompt_lower = prompt.lower()
        
        if 'hospital' in prompt_lower or 'ሆስፒታል' in prompt_lower:
            return "I can help you find nearby hospitals. Please provide your location."
        elif 'ambulance' in prompt_lower or 'አምቡላንስ' in prompt_lower:
            return "Call 907 for ambulance dispatch."
        elif 'emergency' in prompt_lower or 'አደጋ' in prompt_lower:
            return "This is an emergency. Call 907 immediately."
        
        return "I'm here to help with emergencies. Please provide more details."


llm_service = LLMService()