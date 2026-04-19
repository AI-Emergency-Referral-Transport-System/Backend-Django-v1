import logging
from typing import Optional
import base64

logger = logging.getLogger(__name__)


class SpeechToText:
    def __init__(self):
        self.llm_service = None
    
    def transcribe(self, audio_data, language: str = 'en') -> str:
        try:
            from .llm_service import llm_service
            
            if hasattr(audio_data, 'read'):
                audio_bytes = audio_data.read()
            elif isinstance(audio_data, str):
                audio_bytes = base64.b64decode(audio_data)
            else:
                return "Invalid audio format"
            
            prompt = f"Transcribe this audio in {language}:"
            result = llm_service.generate(prompt)
            return result
            
        except Exception as e:
            logger.error(f"STT error: {e}")
            return ""


class TextToSpeech:
    def __init__(self):
        self.provider = None
    
    def synthesize(self, text: str, language: str = 'en') -> Optional[bytes]:
        try:
            if language == 'am':
                text = f"[Amharic] {text}"
            
            return None
            
        except Exception as e:
            logger.error(f"TTS error: {e}")
            return None


stt_service = SpeechToText()
tts_service = TextToSpeech()