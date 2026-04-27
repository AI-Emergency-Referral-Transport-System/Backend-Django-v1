from rest_framework import serializers

from accounts.models import DriverProfile, HospitalProfile, User
from hospitals.models import Hospital


class AdminUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "phone_number",
            "email",
            "role",
            "is_verified",
            "is_active",
            "date_joined",
            "created_at",
        ]
        read_only_fields = ["id", "date_joined", "created_at"]


class AdminHospitalProfileSerializer(serializers.ModelSerializer):
    user = AdminUserSerializer(read_only=True)

    class Meta:
        model = HospitalProfile
        fields = [
            "id",
            "user",
            "hospital_name",
            "address",
            "available_beds",
            "icu_available",
            "oxygen_level",
            "services",
            "registration_status",
            "created_at",
        ]
        read_only_fields = ["id", "user", "created_at"]


class AdminDriverProfileSerializer(serializers.ModelSerializer):
    user = AdminUserSerializer(read_only=True)

    class Meta:
        model = DriverProfile
        fields = [
            "id",
            "user",
            "plate_number",
            "vehicle_type",
            "availability",
            "has_oxygen",
            "has_defibrillator",
            "verification_status",
            "created_at",
        ]
        read_only_fields = ["id", "user", "created_at"]


class AdminDashboardSerializer(serializers.Serializer):
    total_patients = serializers.IntegerField()
    total_drivers = serializers.IntegerField()
    total_hospitals = serializers.IntegerField()
    total_emergencies = serializers.IntegerField()
    pending_hospitals = serializers.IntegerField()
    pending_drivers = serializers.IntegerField()
    active_emergencies = serializers.IntegerField()
    completed_emergencies = serializers.IntegerField()