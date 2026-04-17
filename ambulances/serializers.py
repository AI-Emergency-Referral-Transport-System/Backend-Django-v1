from rest_framework import serializers
from .models import Ambulance

class AmbulanceSerializer(serializers.ModelSerializer):
    # We include nested fields so Flutter doesn't have to make extra API calls
    driver_name = serializers.ReadOnlyField(source="driver.full_name")
    hospital_name = serializers.ReadOnlyField(source="hospital.name")

    class Meta:
        model = Ambulance
        fields = (
            "id",
            "plate_number",  
            "vehicle_type",  #  basic, advanced, or neonatal
            "driver",
            "driver_name",   # Helper for Flutter UI
            "hospital",
            "hospital_name", # Helper for Flutter UI
            "status",
            "latitude",      # Required for Real-time tracking
            "longitude",     #  Required for Real-time tracking
            "has_oxygen",    #  AI Equipment tracking
            "has_defibrillator",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at", "driver_name", "hospital_name")

class AmbulanceStatusUpdateSerializer(serializers.ModelSerializer):
    """
    Specific serializer for the Driver App to change status 
    """
    class Meta:
        model = Ambulance
        fields = ("status", "latitude", "longitude")