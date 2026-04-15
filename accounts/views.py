import random
from datetime import timedelta
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.permissions import IsAuthenticated, AllowAny # Added AllowAny
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User, OTPCode
from .serializers import (
    UserSerializer, 
    RegisterSerializer, 
    VerifyOTPSerializer,
    UserProfileSerializer
)

class RegisterView(APIView):
    """
    Public endpoint to initiate registration/login via phone number.
    """
    permission_classes = [AllowAny]  # FIX: Overrides global IsAuthenticated

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            phone = serializer.validated_data['phone_number']
            role = serializer.validated_data.get('role', User.Role.PATIENT)
            
            user, _ = User.objects.get_or_create(
                phone_number=phone, 
                defaults={'role': role}
            )

            # Mock Logic for Hackathon
            code = "123456" if phone == "+251911111111" else str(random.randint(100000, 999999))

            OTPCode.objects.create(
                user=user,
                code=code,
                expires_at=timezone.now() + timedelta(minutes=5)
            )

            # IMPORTANT: For testing, we print the code to the terminal
            print(f"\n[AUTH DEBUG] OTP for {phone}: {code}\n")
            
            return Response({"message": "OTP sent successfully"}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class VerifyOTPView(APIView):
    """
    Public endpoint to verify OTP and receive JWT tokens.
    """
    permission_classes = [AllowAny]  # FIX: Overrides global IsAuthenticated

    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        if serializer.is_valid():
            phone = serializer.validated_data['phone_number']
            otp_sent = serializer.validated_data['otp']

            otp_record = OTPCode.objects.filter(
                user__phone_number=phone, 
                is_used=False
            ).order_by('-created_at').first()

            if otp_record and not otp_record.is_expired and otp_record.code == otp_sent:
                otp_record.is_used = True
                otp_record.save()
                
                refresh = RefreshToken.for_user(otp_record.user)
                return Response({
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                    "user": UserSerializer(otp_record.user).data
                }, status=status.HTTP_200_OK)
            
            return Response({"error": "Invalid or expired OTP"}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    Protected endpoint: Users can only see their own profile.
    """
    permission_classes = [IsAuthenticated] # Keep this protected
    serializer_class = UserProfileSerializer

    def get_object(self):
        return self.request.user