from rest_framework import serializers

from accounts.models import DriverProfile, HospitalProfile, Profile, User


class ProfileUserSerializer(serializers.ModelSerializer):
    authorization_status = serializers.SerializerMethodField()
    authorization_completed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "phone_number",
            "email",
            "role",
            "is_verified",
            "authorization_status",
            "authorization_completed",
        )
        read_only_fields = fields

    def get_authorization_status(self, obj: User) -> str:
        return obj.get_authorization_status()

    def get_authorization_completed(self, obj: User) -> bool:
        return obj.is_authorization_completed()


class DriverProfileSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="user.profile.full_name", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)
    phone = serializers.CharField(source="user.phone_number", read_only=True)

    class Meta:
        model = DriverProfile
        fields = (
            "id",
            "name",
            "email",
            "phone",
            "plate_number",
            "vehicle_type",
            "availability",
            "has_oxygen",
            "has_defibrillator",
            "verification_status",
            "updated_at",
        )
        read_only_fields = ("id", "verification_status", "updated_at")


class HospitalProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source="user.email", read_only=True)
    phone = serializers.CharField(source="user.phone_number", read_only=True)
    services = serializers.ListField(
        child=serializers.CharField(max_length=128),
        required=False,
    )

    class Meta:
        model = HospitalProfile
        fields = (
            "id",
            "hospital_name",
            "address",
            "email",
            "phone",
            "available_beds",
            "icu_available",
            "oxygen_level",
            "services",
            "registration_status",
            "updated_at",
        )
        read_only_fields = ("id", "registration_status", "updated_at")


class ProfileSerializer(serializers.ModelSerializer):
    user = ProfileUserSerializer(read_only=True)
    driver_profile = DriverProfileSerializer(required=False, allow_null=True)
    hospital_profile = HospitalProfileSerializer(required=False, allow_null=True)

    class Meta:
        model = Profile
        fields = (
            "id",
            "user",
            "full_name",
            "emergency_contact",
            "blood_type",
            "location",
            "driver_profile",
            "hospital_profile",
            "updated_at",
        )
        read_only_fields = ("id", "user", "updated_at")

    def validate(self, attrs):
        attrs = super().validate(attrs)

        request = self.context.get("request")
        if request is None or not request.user.is_authenticated:
            return attrs

        driver_data = attrs.get("driver_profile")
        hospital_data = attrs.get("hospital_profile")
        role = request.user.role

        if role == User.Role.PATIENT and (driver_data is not None or hospital_data is not None):
            raise serializers.ValidationError(
                "Patient profiles do not accept driver or hospital registration fields."
            )
        if role == User.Role.DRIVER and hospital_data is not None:
            raise serializers.ValidationError(
                {"hospital_profile": "Hospital registration fields are only available to hospital admins."}
            )
        if role == User.Role.HOSPITAL_ADMIN and driver_data is not None:
            raise serializers.ValidationError(
                {"driver_profile": "Driver registration fields are only available to drivers."}
            )

        return attrs

    def update(self, instance, validated_data):
        driver_data = validated_data.pop("driver_profile", None)
        hospital_data = validated_data.pop("hospital_profile", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if driver_data is not None:
            driver_profile, _ = DriverProfile.objects.get_or_create(user=instance.user)
            for attr, value in driver_data.items():
                setattr(driver_profile, attr, value)
            driver_profile.save()

        if hospital_data is not None:
            hospital_profile, _ = HospitalProfile.objects.get_or_create(user=instance.user)
            for attr, value in hospital_data.items():
                setattr(hospital_profile, attr, value)
            hospital_profile.save()

        return instance
