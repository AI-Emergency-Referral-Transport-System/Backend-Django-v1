from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from accounts.profiles.views import ProfileRetrieveUpdateAPIView
from accounts.views import (
    ChangePasswordAPIView,
    EmergencyContactDetailAPIView,
    EmergencyContactsListCreateAPIView,
    ForgotPasswordAPIView,
    LoginAPIView,
    OTPRequestAPIView,
    OTPVerifyAPIView,
    PatientRegistrationAPIView,
    ResetPasswordAPIView,
    UpdateLocationAPIView,
    VerifyEmailAPIView,
)


app_name = "accounts"

urlpatterns = [
    # Auth endpoints
    path("register/patient/", PatientRegistrationAPIView.as_view(), name="register-patient"),
    path("login/", LoginAPIView.as_view(), name="login"),
    path("forgot-password/", ForgotPasswordAPIView.as_view(), name="forgot-password"),
    path("reset-password/", ResetPasswordAPIView.as_view(), name="reset-password"),
    path("change-password/", ChangePasswordAPIView.as_view(), name="change-password"),
    path("verify-email/", VerifyEmailAPIView.as_view(), name="verify-email"),
    path("profile/", ProfileRetrieveUpdateAPIView.as_view(), name="profile-detail"),
    path("location/", UpdateLocationAPIView.as_view(), name="update-location"),
    path("emergency-contacts/", EmergencyContactsListCreateAPIView.as_view(), name="emergency-contacts"),
    path("emergency-contacts/<uuid:contact_id>/", EmergencyContactDetailAPIView.as_view(), name="emergency-contact-detail"),
    
    # OTP endpoints (alternative)
    path("otp/request/", OTPRequestAPIView.as_view(), name="otp-request"),
    path("otp/verify/", OTPVerifyAPIView.as_view(), name="otp-verify"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
]