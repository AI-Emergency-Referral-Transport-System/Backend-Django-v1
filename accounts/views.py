import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import permissions, response, status
from rest_framework.exceptions import ValidationError
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.profiles.serializers import ProfileSerializer
from accounts.profiles.services import ensure_profile_bundle
from accounts.serializers import (
    ChangePasswordSerializer,
    EmergencyContactSerializer,
    ForgotPasswordSerializer,
    LocationUpdateSerializer,
    LoginSerializer,
    OTPRequestSerializer,
    OTPVerifySerializer,
    PatientRegistrationSerializer,
    ResetPasswordSerializer,
    UserSerializer,
    VerifyEmailSerializer,
)
from accounts.services.otp_service import OTPService


User = get_user_model()


def _normalize_gender(value: str | None) -> str:
    if not value:
        return ""
    normalized = value.strip().lower()
    mapping = {
        "male": User.Gender.MALE,
        "female": User.Gender.FEMALE,
        "other": User.Gender.OTHER,
    }
    return mapping.get(normalized, "")


class PatientRegistrationAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PatientRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        email = data["email"].lower()

        if User.objects.filter(email=email).exists():
            return response.Response(
                {"success": False, "errors": {"email": ["Email already registered."]}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = User.objects.create_user(
            email=email,
            password=data["password"],
            phone_number=data.get("phone"),
            role=User.Role.PATIENT,
            name=data.get("name", ""),
            age=data.get("age"),
            gender=_normalize_gender(data.get("gender")),
            is_verified=True,
        )

        profile = ensure_profile_bundle(user)
        profile.full_name = data.get("name", "")
        profile.save()

        refresh = RefreshToken.for_user(user)
        return response.Response(
            {
                "success": True,
                "message": "Registration successful",
                "tokens": {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                },
                "user": UserSerializer(user).data,
            },
            status=status.HTTP_201_CREATED,
        )


class LoginAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        email = data["email"].lower()

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return response.Response(
                {"success": False, "errors": {"email": ["Invalid credentials."]}},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not user.check_password(data["password"]):
            return response.Response(
                {"success": False, "errors": {"password": ["Invalid credentials."]}},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        refresh = RefreshToken.for_user(user)
        return response.Response(
            {
                "success": True,
                "message": "Login successful",
                "tokens": {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                },
                "user": UserSerializer(user).data,
                "role": user.role,
            },
            status=status.HTTP_200_OK,
        )


class ForgotPasswordAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"].lower()

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return response.Response(
                {
                    "success": True,
                    "message": "Password reset email sent. Check your email inbox.",
                },
                status=status.HTTP_200_OK,
            )

        token = secrets.token_urlsafe(24)
        user.password_reset_token = token
        user.password_reset_expires = timezone.now() + timedelta(minutes=30)
        user.save(update_fields=["password_reset_token", "password_reset_expires"])

        send_mail(
            subject="Password Reset",
            message=f"Your password reset token: {token}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )

        return response.Response(
            {
                "success": True,
                "message": "Password reset email sent. Check your email inbox.",
            },
            status=status.HTTP_200_OK,
        )


class ResetPasswordAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        token = data["token"]

        user = User.objects.filter(
            password_reset_token=token,
            password_reset_expires__gt=timezone.now(),
        ).first()
        if user is None:
            return response.Response(
                {"success": False, "errors": {"token": ["Invalid or expired token."]}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(data["new_password"])
        user.password_reset_token = ""
        user.password_reset_expires = None
        user.save(update_fields=["password", "password_reset_token", "password_reset_expires"])

        return response.Response(
            {
                "success": True,
                "message": "Password reset successful. You can now login with your new password.",
            },
            status=status.HTTP_200_OK,
        )


class ChangePasswordAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        user = request.user

        if not user.check_password(data["old_password"]):
            return response.Response(
                {"success": False, "errors": {"old_password": ["Incorrect password."]}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(data["new_password"])
        user.save(update_fields=["password"])

        return response.Response(
            {"success": True, "message": "Password changed successfully"},
            status=status.HTTP_200_OK,
        )


class VerifyEmailAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = VerifyEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        token = serializer.validated_data["token"]
        user = User.objects.filter(
            verification_token=token,
            verification_token_expires__gt=timezone.now(),
        ).first()
        if user is None:
            return response.Response(
                {"success": False, "errors": {"token": ["Invalid or expired token."]}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.is_verified = True
        user.verification_token = ""
        user.verification_token_expires = None
        user.save(update_fields=["is_verified", "verification_token", "verification_token_expires"])
        return response.Response(
            {"success": True, "message": "Email verified successfully"},
            status=status.HTTP_200_OK,
        )


class ProfileRetrieveUpdateAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        profile = ensure_profile_bundle(request.user)
        return response.Response(ProfileSerializer(profile).data, status=status.HTTP_200_OK)

    def patch(self, request):
        profile = ensure_profile_bundle(request.user)
        serializer = ProfileSerializer(profile, data=request.data, partial=True, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return response.Response(serializer.data, status=status.HTTP_200_OK)


class UpdateLocationAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = LocationUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        request.user.latitude = serializer.validated_data["latitude"]
        request.user.longitude = serializer.validated_data["longitude"]
        request.user.save(update_fields=["latitude", "longitude"])

        return response.Response(
            {"success": True, "message": "Location updated successfully"},
            status=status.HTTP_200_OK,
        )


class EmergencyContactsListCreateAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        contacts = request.user.emergency_contacts.all()
        serializer = EmergencyContactSerializer(contacts, many=True)
        return response.Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = EmergencyContactSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        is_primary = serializer.validated_data.get("is_primary", False)
        if is_primary:
            request.user.emergency_contacts.update(is_primary=False)
        elif not request.user.emergency_contacts.exists():
            is_primary = True

        serializer.save(user=request.user, is_primary=is_primary)
        return response.Response(
            {"success": True, "message": "Contact created successfully"},
            status=status.HTTP_201_CREATED,
        )


class EmergencyContactDetailAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, contact_id):
        contact = get_object_or_404(request.user.emergency_contacts.all(), id=contact_id)
        contact.delete()
        return response.Response(
            {"success": True, "message": "Contact deleted successfully"},
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
        ensure_profile_bundle(user)
        OTPService().request_otp(user)

        return response.Response(
            {"detail": "Verification code sent successfully."},
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
