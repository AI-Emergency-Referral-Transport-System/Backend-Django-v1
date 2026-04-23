from django.contrib.auth import get_user_model
from rest_framework import permissions, response, status
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView

from accounts.profiles.serializers import ProfileSerializer
from accounts.profiles.services import ensure_profile_bundle
from accounts.serializers import OTPRequestSerializer, OTPVerifySerializer, UserSerializer
from accounts.services.otp_service import OTPService


User = get_user_model()


class AuthRootAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, *args, **kwargs):
        return response.Response(
            {
                "message": "Auth API is available.",
                "endpoints": {
                    "signup": "/api/v1/auth/signup/",
                    "otp_request": "/api/v1/auth/otp/request/",
                    "otp_verify": "/api/v1/auth/otp/verify/",
                    "token_refresh": "/api/v1/auth/token/refresh/",
                    "profile": "/api/v1/auth/profile/",
                },
            },
            status=status.HTTP_200_OK,
        )


class OTPRequestAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = OTPRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user, _ = User.objects.get_or_create(
            email=serializer.validated_data["email"],
            defaults={"role": User.Role.PATIENT},
        )
        profile = ensure_profile_bundle(user)
        OTPService().request_otp(user)

        return response.Response(
            {
                "detail": "Verification code sent successfully.",
                "profile": ProfileSerializer(profile).data,
            },
            status=status.HTTP_202_ACCEPTED,
        )


class OTPVerifyAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = OTPVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = User.objects.filter(email=serializer.validated_data["email"]).first()
        if user is None:
            raise ValidationError({"code": "Invalid or expired verification code."})

        OTPService().verify_otp(user=user, code=serializer.validated_data["code"])
        profile = ensure_profile_bundle(user)

        refresh = RefreshToken.for_user(user)
        return response.Response(
            {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "user": UserSerializer(user).data,
                "profile": ProfileSerializer(profile).data,
            },
            status=status.HTTP_200_OK,
        )
