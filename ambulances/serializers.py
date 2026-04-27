from rest_framework import serializers
from .models import Ambulance, Driver


class DriverCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255, required=False)
    email = serializers.EmailField()
    phone = serializers.CharField(max_length=32, required=False)
    license_number = serializers.CharField(max_length=50, required=False)
    license_expiry = serializers.DateField(required=False, allow_null=True)
    experience_years = serializers.IntegerField(default=0, required=False)
    ambulance_id = serializers.UUIDField(required=False, allow_null=True)


class AmbulanceSerializer(serializers.ModelSerializer):
    driver_name = serializers.ReadOnlyField(source="driver.profile.full_name")
    hospital_name = serializers.ReadOnlyField(source="hospital.name")

    class Meta:
        model = Ambulance
        fields = (
            "id",
            "plate_number",
            "driver",
            "driver_name",
            "hospital",
            "hospital_name",
            "status",
            "organization",
            "phone",
            "equipment",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at", "driver_name", "hospital_name")


class AmbulanceStatusUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ambulance
        fields = ("status",)