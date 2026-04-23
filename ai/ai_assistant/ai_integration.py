import math
import logging
from typing import Dict, List, Any, Optional, Tuple
from django.conf import settings
logger = logging.getLogger(__name__)
class EmergencyDispatchAI:
    def __init__(self):
        self.map_service = None
        self.ambulance_service = None
        self.hospital_service = None
        self._init_services()
    def _init_services(self):
        try:
            from .services import MapService, AmbulanceService, HospitalService
            self.map_service = MapService()
            self.ambulance_service = AmbulanceService()
            self.hospital_service = HospitalService()
        except Exception as e:
            logger.error(f"Failed to init services: {e}")
    def create_emergency_dispatch(
        self,
        user_id: str,
        emergency_type: str,
        patient_location: Dict,
        priority: str = 'medium',
        language: str = 'en',
        description: str = ''
    ) -> Dict:
        lat = patient_location.get('latitude')
        lon = patient_location.get('longitude')
        if not lat or not lon:
            return {'error': 'Location required', 'success': False}
        nearest_ambulance = None
        if self.ambulance_service:
            nearest_ambulance = self.ambulance_service.get_nearest_ambulance(lat, lon)
            emergency_ambulances = self.ambulance_service.get_emergency_ambulances(emergency_type, lat, lon)
        else:
            emergency_ambulances = []
        nearest_hospital = None
        if self.hospital_service:
            nearest_hospital = self.hospital_service.get_nearest_hospital(lat, lon)
            suitable_hospitals = self.hospital_service.get_hospitals_by_emergency_type(emergency_type, lat, lon)
        else:
            suitable_hospitals = []
        priority_score = self._calculate_priority_score(emergency_type, priority)
        dispatch_data = {
            'success': True,
            'emergency_id': self._generate_emergency_id(),
            'priority': priority,
            'priority_score': priority_score,
            'emergency_type': emergency_type,
            'description': description,
            'patient_location': {
                'latitude': lat,
                'longitude': lon,
                'maps_link': f"https://maps.google.com/?q={lat},{lon}",
                'embed_map': f"https://www.google.com/maps?q={lat},{lon}&z=15&output=embed" if self.map_service else None
            },
            'response': {
                'ambulance': {
                    'dispatched': nearest_ambulance is not None,
                    'nearest': nearest_ambulance,
                    'alternatives': emergency_ambulances[:3],
                    'one_tap_call': '907'
                },
                'hospital': {
                    'recommended': nearest_hospital,
                    'suitable': suitable_hospitals[:3],
                    'alert_status': 'pending'
                },
                'eta': nearest_ambulance.get('eta_minutes') if nearest_ambulance else None,
                'distance': nearest_ambulance.get('distance_km') if nearest_ambulance else None
            },
            'actions': self._get_emergency_actions(emergency_type, priority, language),
            'language': language
        }
        if language == 'am':
            dispatch_data['amharic'] = self._get_amharic_instructions(emergency_type, priority)
        return dispatch_data
    def _calculate_priority_score(self, emergency_type: str, priority: str) -> int:
        priority_map = {
            'critical': 3,
            'high': 2,
            'medium': 1,
            'low': 0
        }
        base_score = priority_map.get(priority.lower(), 1)
        critical_emergencies = ['cardiac', 'stroke', 'respiratory', 'unconscious']
        if emergency_type in critical_emergencies:
            base_score += 2
        return base_score
    def _generate_emergency_id(self) -> str:
        import uuid
        return f"EMR-{uuid.uuid4().hex[:8].upper()}"
    def _get_emergency_actions(self, emergency_type: str, priority: str, language: str) -> List[Dict]:
        actions = []
        if priority == 'critical':
            actions.append({
                'type': 'call',
                'number': '907',
                'label': 'Call Ambulance' if language == 'en' else 'አምቡላንስ ይደውሉ',
                'action': 'tel:907'
            })
        actions.append({
            'type': 'sms',
            'number': '907',
            'label': 'Send Location SMS' if language == 'en' else 'ቦታ ላክ ስልክ',
            'action': 'sms:907'
        })
        actions.append({
            'type': 'map',
            'label': 'Open Maps' if language == 'en' else 'ካርታ ክፈት',
            'action': 'open_maps'
        })
        return actions
    def _get_amharic_instructions(self, emergency_type: str, priority: str) -> Dict:
        instructions = {
            'critical': 'ይህ አስቸኳይ ነው! ወዲያውኑ የ907ን ይደውሉ',
            'high': 'አስቸኳይ ነው። አምቡላንስ የሚጣውን ይጠብቡ',
            'medium': 'እንደውለን አምቡላንስ ይሰጣልዎት',
            'low': 'አምቡላንስ ይመጣልዎት'
        }
        return {
            'message': instructions.get(priority, instructions['medium']),
            'one_tap': '907',
            'sms_format': 'EMERGENCY [location]'
        }
    def check_ambulance_availability(self, latitude: float, longitude: float) -> Dict:
        if not self.ambulance_service:
            return {'available': False, 'count': 0}
        ambulances = self.ambulance_service.get_available_ambulances(latitude, longitude)
        return {
            'available': len(ambulances) > 0,
            'count': len(ambulances),
            'nearest': ambulances[0] if ambulances else None,
            'all': ambulances[:5]
        }
    def get_hospital_capacity(self, latitude: float, longitude: float, emergency_type: str) -> Dict:
        if not self.hospital_service:
            return {'available': False, 'hospitals': []}
        hospitals = self.hospital_service.get_hospitals_by_emergency_type(emergency_type, latitude, longitude)
        return {
            'available': len(hospitals) > 0,
            'count': len(hospitals),
            'recommended': hospitals[0] if hospitals else None,
            'all': hospitals[:5]
        }
class AIEmergencyAnalyzer:
    def __init__(self):
        self.emergency_keywords = {
            'cardiac': ['chest pain', 'heart', 'heart attack', 'ልብ', 'የልብ ህመም'],
            'respiratory': ['breathing', 'breath', 'asthma', 'choking', 'መተንፈስ', 'ማስተንፈስ'],
            'trauma': ['injury', 'injured', 'hurt', 'accident', 'ጉዳት', 'ቁስል', 'አደጋ'],
            'stroke': ['stroke', 'paralysis', 'face drooping', 'ስትሮክ'],
            'burn': ['burn', 'fire', 'ቃጠሎ', 'እሣት'],
            'bleeding': ['bleeding', 'blood', 'ደም', 'ማፈን'],
            'unconscious': ['unconscious', 'fainted', 'ራሱን ስቶ', 'not responding'],
            'pregnancy': ['pregnant', 'labor', 'delivery', 'ነፍሰ ጡር', 'ምጥ'],
            'poisoning': ['poison', 'toxic', 'ስትራይት'],
        }
    def analyze_emergency_text(self, text: str, language: str = 'en') -> Dict:
        text_lower = text.lower()
        detected_type = 'other'
        confidence = 0.5
        for emergency_type, keywords in self.emergency_keywords.items():
            matches = sum(1 for kw in keywords if kw in text_lower)
            if matches > 0:
                detected_type = emergency_type
                confidence = min(0.95, 0.5 + (matches * 0.15))
                break
        priority = self._determine_priority(detected_type, text_lower)
        needs_immediate = priority in ['critical', 'high']
        return {
            'detected_type': detected_type,
            'confidence': confidence,
            'priority': priority,
            'needs_immediate_dispatch': needs_immediate,
            'keywords_found': self._extract_keywords(text_lower),
            'language': language
        }
    def _determine_priority(self, emergency_type: str, text_lower: str) -> str:
        critical_types = ['cardiac', 'stroke', 'unconscious', 'respiratory']
        high_types = ['trauma', 'bleeding', 'burn', 'pregnancy']
        if emergency_type in critical_types:
            return 'critical'
        elif emergency_type in high_types:
            return 'high'
        elif 'accident' in text_lower or 'emergency' in text_lower:
            return 'high'
        return 'medium'
    def _extract_keywords(self, text_lower: str) -> List[str]:
        found = []
        for emergency_type, keywords in self.emergency_keywords.items():
            for kw in keywords:
                if kw in text_lower:
                    found.append(kw)
        return found[:5]
class EmergencyNotificationService:
    @staticmethod
    def create_notification_payload(dispatch_data: Dict, language: str = 'en') -> Dict:
        emergency_type = dispatch_data.get('emergency_type', 'other')
        priority = dispatch_data.get('priority', 'medium')
        if language == 'am':
            messages = {
                'critical': 'አስቸኳይ ድንገተኛ ተከስቷል!',
                'high': 'ድንገተኛ ተከስቷል!',
                'medium': 'ድንገተኛ ጥያቄ ተላኪያል!',
                'low': 'ጥያቄ ተላኪያል!'
            }
        else:
            messages = {
                'critical': 'URGENT emergency dispatched!',
                'high': 'Emergency case dispatched!',
                'medium': 'Emergency request submitted!',
                'low': 'Request submitted!'
            }
        return {
            'title': messages.get(priority, messages['medium']),
            'body': f"Emergency: {emergency_type.upper()}",
            'priority': priority,
            'sound': 'default' if priority in ['critical', 'high'] else 'normal',
            'data': dispatch_data
        }
    @staticmethod
    def send_sms_alert(phone: str, emergency_data: Dict, language: str = 'en') -> str:
        lat = emergency_data.get('patient_location', {}).get('latitude')
        lon = emergency_data.get('patient_location', {}).get('longitude')
        emergency_type = emergency_data.get('emergency_type', 'emergency')
        location_str = f" https://maps.google.com/?q={lat},{lon}" if lat and lon else ""
        if language == 'am':
            message = f"አደጋ: {emergency_type.upper()}{location_str} - 907ን ይደውሉ"
        else:
            message = f"EMERGENCY: {emergency_type.upper()}{location_str} - Call 907"
        return message
class LocationService:
    @staticmethod
    def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        R = 6371
        d_lat = math.radians(lat2 - lat1)
        d_lon = math.radians(lon2 - lon1)
        a = math.sin(d_lat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lon / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c
    @staticmethod
    def get_eta(distance_km: float, speed_kmh: int = 40) -> int:
        if distance_km <= 0:
            return 1
        minutes = (distance_km / speed_kmh) * 60
        return max(1, int(minutes))
    @staticmethod
    def format_location_for_display(lat: float, lon: float, language: str = 'en') -> str:
        if language == 'am':
            return f"ቦታ: {lat:.6f}, {lon:.6f}"
        return f"Location: {lat:.6f}, {lon:.6f}"
emergency_dispatch_ai = EmergencyDispatchAI()
emergency_analyzer = AIEmergencyAnalyzer()
notification_service = EmergencyNotificationService()
location_service = LocationService()