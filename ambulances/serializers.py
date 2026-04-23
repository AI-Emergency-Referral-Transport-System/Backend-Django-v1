from rest_framework import serializers
from .models import Ambulance

class AmbulanceSerializer(serializers.ModelSerializer):
    # We include nested fields so Flutter doesn't have to make extra API calls
    driver_name = serializers.ReadOnlyField(source="driver.profile.full_name")
    hospital_name = serializers.ReadOnlyField(source="hospital.name")

    class Meta:
        model = Ambulance
        fields = (
            "id",
            "plate_number",  
            "driver",
            "driver_name",   # Helper for Flutter UI
            "hospital",
            "hospital_name", # Helper for Flutter UI
            "status",
            "current_location", # Required for Real-time tracking
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
        fields = ("status", "current_location")
