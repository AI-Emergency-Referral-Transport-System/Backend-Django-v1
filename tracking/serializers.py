from rest_framework import serializers
from rest_framework_gis.fields import GeometryField

from hospitals.serializers import HospitalSerializer
from accounts.serializers import UserSerializer
from emergencies.models import Emergency

class EmergencySerializer(serializers.ModelSerializer):
    # Nesting the patient and hospital data
    patient = UserSerializer(read_only=True)
    selected_hospital = HospitalSerializer(read_only=True)
    
    # Manually exposing coordinates from the PostGIS Point
    patient_lat = serializers.FloatField(source='patient_location.y', read_only=True)
    patient_lon = serializers.FloatField(source='patient_location.x', read_only=True)

    class Meta:
        model = Emergency
        fields = [
            'id', 'status', 'is_resolved', 'patient', 
            'selected_hospital', 'patient_lat', 'patient_lon', 'created_at'
        ]