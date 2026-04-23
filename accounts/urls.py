from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from accounts.profiles.views import ProfileRetrieveUpdateAPIView
from accounts.views import AuthRootAPIView, OTPRequestAPIView, OTPVerifyAPIView


app_name = "accounts"

urlpatterns = [
    path("", AuthRootAPIView.as_view(), name="auth-root"),
    path("signup/", OTPRequestAPIView.as_view(), name="signup"),
    path("otp/request/", OTPRequestAPIView.as_view(), name="otp-request-clean"),
    path("otp/verify/", OTPVerifyAPIView.as_view(), name="otp-verify-clean"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token-refresh-clean"),
    path("auth/otp/request/", OTPRequestAPIView.as_view(), name="otp-request"),
    path("auth/otp/verify/", OTPVerifyAPIView.as_view(), name="otp-verify"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("profile/", ProfileRetrieveUpdateAPIView.as_view(), name="profile-detail"),
]
