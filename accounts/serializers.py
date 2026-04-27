from rest_framework import serializers

from accounts.profiles.serializers import (
    DriverProfileSerializer,
    HospitalProfileSerializer,
    ProfileSerializer,
    ProfileUserSerializer,
)


UserSerializer = ProfileUserSerializer


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
    "DriverProfileSerializer",
    "HospitalProfileSerializer",
    "OTPRequestSerializer",
    "OTPVerifySerializer",
    "ProfileSerializer",
    "UserSerializer",
]
