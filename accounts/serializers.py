from rest_framework import serializers

from accounts.profiles.serializers import (
    DriverProfileSerializer,
    HospitalProfileSerializer,
    ProfileSerializer,
    ProfileUserSerializer,
)


UserSerializer = ProfileUserSerializer


class OTPRequestSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=32)

    def validate_phone_number(self, value: str) -> str:
        phone_number = value.strip()
        if not phone_number:
            raise serializers.ValidationError("Phone number is required.")
        return phone_number


class OTPVerifySerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=32)
    code = serializers.CharField(max_length=6, min_length=6)

    def validate_phone_number(self, value: str) -> str:
        phone_number = value.strip()
        if not phone_number:
            raise serializers.ValidationError("Phone number is required.")
        return phone_number

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
