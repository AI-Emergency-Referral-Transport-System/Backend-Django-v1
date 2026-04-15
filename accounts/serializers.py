from rest_framework import serializers
from .models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'phone_number', 'role', 'first_name', 'last_name']

class RegisterSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=32)
    role = serializers.ChoiceField(choices=User.Role.choices, required=False)
    first_name = serializers.CharField(required=False)

class VerifyOTPSerializer(serializers.Serializer):
    phone_number = serializers.CharField()
    otp = serializers.CharField(max_length=6)

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'email', 'blood_type', 
            'allergies', 'medical_history', 'emergency_contacts', 
            'preferred_language'
        ]
        read_only_fields = ['phone_number', 'role']