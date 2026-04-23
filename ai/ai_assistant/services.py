import math
import logging
from typing import Dict, List, Any, Optional, Tuple
from decimal import Decimal

logger = logging.getLogger(__name__)


class MapService:
    @staticmethod
    def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        R = 6371
        d_lat = math.radians(lat2 - lat1)
        d_lon = math.radians(lon2 - lon1)
        a = math.sin(d_lat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lon / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c
    @staticmethod
    def get_eta(minutes_distance: float, mode: str = 'driving') -> int:
        speeds = {'driving': 40, 'walking': 5, 'cycling': 15}
        speed = speeds.get(mode, 40)
        return max(1, int(minutes_distance / speed * 60))
    @staticmethod
    def get_direction_url(origin: Tuple[float, float], destination: Tuple[float, float]) -> str:
        return f"https://www.google.com/maps/dir/{origin[0]},{origin[1]}/{destination[0]},{destination[1]}"
    @staticmethod
    def get_embed_url(lat: float, lon: float, zoom: int = 15) -> str:
        return f"https://www.google.com/maps?q={lat},{lon}&z={zoom}&output=embed"
class AmbulanceService:
    def __init__(self):
        from ...ambulances.models import Ambulance, Driver
        from ..users.models import User
        self.Ambulance = Ambulance
        self.Driver = Driver
        self.User = User
    def get_available_ambulances(self, latitude: float, longitude: float, radius_km: float = 50) -> List[Dict]:
        ambulances = self.Ambulance.objects.filter(
            status='available',
            verification_status='approved'
        ).exclude(latitude__isnull=True, longitude__isnull=True)
        results = []
        for amb in ambulances:
            distance = MapService.calculate_distance(
                latitude, longitude,
                float(amb.latitude), float(amb.longitude)
            )
            if distance <= radius_km:
                results.append({
                    'id': str(amb.id),
                    'plate_number': amb.plate_number,
                    'distance_km': round(distance, 2),
                    'eta_minutes': MapService.get_eta(distance),
                    'latitude': float(amb.latitude),
                    'longitude': float(amb.longitude),
                    'phone': getattr(amb, 'phone', ''),
                })
        results.sort(key=lambda x: x['distance_km'])
        return results[:10]

    def get_nearest_ambulance(self, latitude: float, longitude: float) -> Optional[Dict]:
        ambulances = self.get_available_ambulances(latitude, longitude, 50)
        return ambulances[0] if ambulances else None

    def get_emergency_ambulances(self, emergency_type: str, latitude: float, longitude: float) -> List[Dict]:
        return self.get_available_ambulances(latitude, longitude, 50)


class HospitalService:
    def __init__(self):
        from ...hospitals.models import Hospital
        self.Hospital = Hospital

    def get_nearby_hospitals(self, latitude: float, longitude: float, radius_km: float = 50) -> List[Dict]:
        hospitals = self.Hospital.objects.all()
        results = []
        for hosp in hospitals:
            if not hosp.latitude or not hosp.longitude:
                continue
            distance = MapService.calculate_distance(
                latitude, longitude,
                float(hosp.latitude), float(hosp.longitude)
            )
            if distance <= radius_km:
                results.append({
                    'id': str(hosp.id),
                    'name': hosp.name,
                    'distance_km': round(distance, 2),
                    'eta_minutes': MapService.get_eta(distance),
                    'latitude': float(hosp.latitude),
                    'longitude': float(hosp.longitude),
                    'phone': getattr(hosp, 'phone', ''),
                    'available_beds': getattr(hosp, 'available_beds', 0),
                })
        results.sort(key=lambda x: x['distance_km'])
        return results[:10]

    def get_nearest_hospital(self, latitude: float, longitude: float) -> Optional[Dict]:
        hospitals = self.get_nearby_hospitals(latitude, longitude, 50)
        return hospitals[0] if hospitals else None

    def get_hospitals_by_emergency_type(self, emergency_type: str, latitude: float, longitude: float) -> List[Dict]:
        return self.get_nearby_hospitals(latitude, longitude, 50)


class UserProfileService:
    def __init__(self):
        from accounts.models import User
        self.User = User

    def get_user_profile(self, user_id: str) -> Optional[Dict]:
        try:
            user = self.User.objects.get(id=user_id)
            return {
                'id': str(user.id),
                'name': user.get_full_name() or user.username,
                'phone': getattr(user, 'phone', ''),
            }
        except Exception:
            return None

    def get_emergency_contacts(self, user_id: str) -> List[Dict]:
        return []

    def get_primary_contact(self, user_id: str) -> Optional[Dict]:
        return None

    def get_user_location(self, user_id: str) -> Optional[Dict]:
        return None