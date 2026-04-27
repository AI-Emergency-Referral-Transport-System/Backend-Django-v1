from rest_framework import serializers
from rest_framework_gis.fields import GeometryField

from hospitals.models import Hospital


class HospitalRegistrationSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    facility_type = serializers.ChoiceField(
        choices=["hospital", "clinic", "health_center"],
        default="hospital"
    )
    address = serializers.CharField(max_length=255, required=False, allow_blank=True)
    city = serializers.CharField(max_length=100, required=False, allow_blank=True)
    latitude = serializers.FloatField(required=False, allow_null=True)
    longitude = serializers.FloatField(required=False, allow_null=True)
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_null=True)
    admin_email = serializers.EmailField(required=False)
    admin_password = serializers.CharField(min_length=6, write_only=True, required=False)
    admin_password_confirm = serializers.CharField(min_length=6, write_only=True, required=False)
    total_beds = serializers.IntegerField(default=0, required=False)
    total_icu_beds = serializers.IntegerField(default=0, required=False)
    has_emergency = serializers.BooleanField(default=False, required=False)
    has_icu = serializers.BooleanField(default=False, required=False)
    has_surgery = serializers.BooleanField(default=False, required=False)

    def validate(self, data):
        if data.get("admin_password") != data.get("admin_password_confirm"):
            raise serializers.ValidationError({"admin_password_confirm": "Passwords do not match."})
        return data


class HospitalSerializer(serializers.ModelSerializer):
    location = GeometryField(required=False)
    distance_km = serializers.FloatField(required=False, read_only=True)
    latitude = serializers.SerializerMethodField()
    longitude = serializers.SerializerMethodField()
    has_emergency = serializers.BooleanField(required=False)
    has_icu = serializers.BooleanField(required=False)
    has_surgery = serializers.BooleanField(required=False)

    class Meta:
        model = Hospital
        fields = (
            "id",
            "name",
            "facility_type",
            "address",
            "city",
            "region",
            "latitude",
            "longitude",
            "phone",
            "email",
            "admin",
            "location",
            "total_beds",
            "available_beds",
            "occupied_beds",
            "total_icu_beds",
            "available_icu_beds",
            "occupied_icu_beds",
            "oxygen_level",
            "services",
            "departments",
            "specialties",
            "has_emergency",
            "has_icu",
            "has_surgery",
            "has_cardiology",
            "has_trauma",
            "has_maternity",
            "has_neonatal",
            "is_available",
            "verification_status",
            "distance_km",
            "created_at",
        )
        read_only_fields = ("id", "created_at")

    def get_latitude(self, obj):
        if obj.location:
            return obj.location.y
        return None

    def get_longitude(self, obj):
        if obj.location:
            return obj.location.x
        return None


class HospitalListSerializer(serializers.ModelSerializer):
    latitude = serializers.SerializerMethodField()
    longitude = serializers.SerializerMethodField()

    class Meta:
        model = Hospital
        fields = (
            "id",
            "name",
            "facility_type",
            "address",
            "city",
            "latitude",
            "longitude",
            "phone",
            "available_beds",
            "total_beds",
            "verification_status",
        )
        read_only_fields = ("id",)

    def get_latitude(self, obj):
        if obj.location:
            return obj.location.y
        return None

    def get_longitude(self, obj):
        if obj.location:
            return obj.location.x
        return None


class HospitalResourceUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hospital
        fields = (
            "available_beds",
            "occupied_beds",
            "available_icu_beds",
            "occupied_icu_beds",
            "oxygen_level",
            "services",
            "has_cardiology",
            "has_trauma",
            "is_available",
        )


class HospitalResourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hospital
        fields = (
            "available_beds",
            "total_beds",
            "available_icu_beds",
            "total_icu_beds",
            "has_emergency",
            "has_icu",
            "has_surgery",
        )
