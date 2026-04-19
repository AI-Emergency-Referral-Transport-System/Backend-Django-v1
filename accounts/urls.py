from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from accounts.profiles.views import ProfileRetrieveUpdateAPIView
from accounts.views import OTPRequestAPIView, OTPVerifyAPIView

urlpatterns = [
    path("otp/request/", OTPRequestAPIView.as_view(), name="otp-request"),
    path("otp/verify/", OTPVerifyAPIView.as_view(), name="otp-verify"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("profile/", ProfileRetrieveUpdateAPIView.as_view(), name="profile"),
]
