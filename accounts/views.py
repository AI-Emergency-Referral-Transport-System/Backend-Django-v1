from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from rest_framework import permissions, response, status
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView

from accounts.profiles.serializers import ProfileSerializer
from accounts.profiles.services import ensure_profile_bundle
from accounts.serializers import (
    ChangePasswordSerializer,
    ForgotPasswordSerializer,
    LoginSerializer,
    LocationUpdateSerializer,
    OTPRequestSerializer,
    OTPVerifySerializer,
    PatientRegistrationSerializer,
    ResetPasswordSerializer,
    UserSerializer,
)
from accounts.services.otp_service import OTPService


User = get_user_model()


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

        token = default_token_generator.make_token(user)
        from django.core.mail import send_mail

        send_mail(
            subject="Password Reset",
            message=f"Your password reset token: {token}",
            from_email="no-reply@ai-emergency.local",
            recipient_list=[email],
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

        user = User.objects.filter(email__isnull=False).first()
        if user is None or not default_token_generator.check_token(user, token):
            return response.Response(
                {"success": False, "errors": {"token": ["Invalid or expired token."]}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(data["new_password"])
        user.save()

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
        user.save()

        return response.Response(
            {"success": True, "message": "Password changed successfully"},
            status=status.HTTP_200_OK,
        )


class VerifyEmailAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        from accounts.serializers import VerifyEmailSerializer

        serializer = VerifyEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        token = serializer.validated_data["token"]
        return response.Response(
            {"success": True, "message": "Email verified successfully"},
            status=status.HTTP_200_OK,
        )


class ProfileRetrieveUpdateAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    renderer_classes = [permissions.AllowAny]

    def get(self, request):
        profile = request.user.profile
        return response.Response(UserSerializer(request.user).data, status=status.HTTP_200_OK)

    def patch(self, request):
        profile = request.user.profile
        serializer = ProfileSerializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return response.Response(
            {"success": True, "message": "Profile updated successfully"},
            status=status.HTTP_200_OK,
        )


class UpdateLocationAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = LocationUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        return response.Response(
            {"success": True, "message": "Location updated successfully"},
            status=status.HTTP_200_OK,
        )


class EmergencyContactsListCreateAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from accounts.models import EmergencyContact

        contacts = EmergencyContact.objects.filter(user=request.user)
        from accounts.serializers import EmergencyContactSerializer

        serializer = EmergencyContactSerializer(contacts, many=True)
        return response.Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        from accounts.models import EmergencyContact
        from accounts.serializers import EmergencyContactSerializer

        serializer = EmergencyContactSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
        return response.Response(
            {"success": True, "message": "Contact created successfully"},
            status=status.HTTP_201_CREATED,
        )


class EmergencyContactDetailAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, contact_id):
        from accounts.models import EmergencyContact
        from django.shortcuts import get_object_or_404

        contact = get_object_or_404(EmergencyContact, id=contact_id, user=request.user)
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
        profile = ensure_profile_bundle(user)
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