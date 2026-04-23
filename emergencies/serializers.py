from rest_framework import serializers
from rest_framework_gis.fields import GeometryField

from emergencies.models import Emergency


class EmergencySerializer(serializers.ModelSerializer):
    patient_location = GeometryField(required=False, allow_null=True)

    class Meta:
        model = Emergency
        fields = (
            "id",
            "patient",
            "assigned_ambulance",
            "selected_hospital",
            "emergency_type",
            "priority",
            "status",
            "patient_location",
            "patient_description",
            "completed_at",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "patient", "status", "completed_at", "created_at", "updated_at")


class EmergencyDetailSerializer(serializers.ModelSerializer):
    patient_location = GeometryField(required=False, allow_null=True)
    patient_name = serializers.CharField(source="patient.profile.full_name", read_only=True)
    hospital_name = serializers.CharField(source="selected_hospital.name", read_only=True, default=None)

    class Meta:
        model = Emergency
        fields = (
            "id",
            "patient",
            "patient_name",
            "assigned_ambulance",
            "selected_hospital",
            "hospital_name",
            "emergency_type",
            "priority",
            "status",
            "patient_location",
            "patient_description",
            "completed_at",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class EmergencySelectHospitalSerializer(serializers.Serializer):
    """Accepts a hospital ID so the patient can confirm their chosen hospital."""
    hospital_id = serializers.UUIDField()


class EmergencyNotesUpdateSerializer(serializers.Serializer):
    patient_description = serializers.CharField()
