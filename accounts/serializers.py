from rest_framework import serializers

from accounts.models import EmergencyContact
from accounts.profiles.serializers import (
    DriverProfileSerializer,
    HospitalProfileSerializer,
    ProfileSerializer,
    ProfileUserSerializer,
)


UserSerializer = ProfileUserSerializer


class PatientRegistrationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    name = serializers.CharField(max_length=255, required=False, allow_blank=True)
    password = serializers.CharField(min_length=6, write_only=True)
    password_confirm = serializers.CharField(min_length=6, write_only=True)
    phone = serializers.CharField(max_length=32, required=False, allow_blank=True)
    age = serializers.IntegerField(required=False, allow_null=True)
    gender = serializers.ChoiceField(
        choices=["Male", "Female", "Other"],
        required=False,
        allow_null=True
    )

    def validate(self, data):
        if data.get("password") != data.get("password_confirm"):
            raise serializers.ValidationError({"password_confirm": "Passwords do not match."})
        return data


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()


class ResetPasswordSerializer(serializers.Serializer):
    token = serializers.CharField(write_only=True)
    new_password = serializers.CharField(min_length=6, write_only=True)
    new_password_confirm = serializers.CharField(min_length=6, write_only=True)

    def validate(self, data):
        if data.get("new_password") != data.get("new_password_confirm"):
            raise serializers.ValidationError({"new_password_confirm": "Passwords do not match."})
        return data


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(min_length=6, write_only=True)
    new_password_confirm = serializers.CharField(min_length=6, write_only=True)

    def validate(self, data):
        if data.get("new_password") != data.get("new_password_confirm"):
            raise serializers.ValidationError({"new_password_confirm": "Passwords do not match."})
        return data


class VerifyEmailSerializer(serializers.Serializer):
    token = serializers.CharField()


class LocationUpdateSerializer(serializers.Serializer):
    latitude = serializers.FloatField(min_value=-90, max_value=90)
    longitude = serializers.FloatField(min_value=-180, max_value=180)


class EmergencyContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmergencyContact
        fields = ["id", "name", "phone", "relationship", "is_primary"]
        read_only_fields = ["id"]


class OTPRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value: str) -> str:
        email = value.strip().lower()
        if not email:
            raise serializers.ValidationError("Email is required.")
        return email


class OTPVerifySerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6, min_length=6)

    def validate_email(self, value: str) -> str:
        email = value.strip().lower()
        if not email:
            raise serializers.ValidationError("Email is required.")
        return email

    def validate_code(self, value: str) -> str:
        code = value.strip()
        if not code.isdigit():
            raise serializers.ValidationError("Verification code must contain digits only.")
        return code


__all__ = [
    "ChangePasswordSerializer",
    "DriverProfileSerializer",
    "EmergencyContactSerializer",
    "ForgotPasswordSerializer",
    "HospitalProfileSerializer",
    "LocationUpdateSerializer",
    "LoginSerializer",
    "OTPRequestSerializer",
    "OTPVerifySerializer",
    "PatientRegistrationSerializer",
    "ProfileSerializer",
    "ResetPasswordSerializer",
    "UserSerializer",
    "VerifyEmailSerializer",
]
