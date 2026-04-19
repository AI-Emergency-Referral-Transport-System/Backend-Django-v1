import secrets
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError

from accounts.models import OTPCode, User
from accounts.services.notification_service import send_otp_notification


class OTPService:
    expiry_window = timedelta(minutes=5)
    rate_limit_window = timedelta(minutes=10)
    max_requests_per_window = 3

    def request_otp(self, user: User) -> OTPCode:
        if not user.is_active:
            raise PermissionDenied("User account is inactive.")

        self._enforce_rate_limit(user)
        OTPCode.objects.filter(user=user, is_used=False).update(is_used=True)

        raw_code = f"{secrets.randbelow(10**6):06d}"
        otp = OTPCode(
            user=user,
            expires_at=timezone.now() + self.expiry_window,
        )
        otp.set_code(raw_code)
        otp.save()

        send_otp_notification(user=user, otp_code=raw_code)
        if settings.DEBUG and getattr(settings, "OTP_DEBUG_OUTPUT", True):
            print(f"[OTP DEBUG] {user.phone_number}: {raw_code}")
        return otp

    @transaction.atomic
    def verify_otp(self, user: User, code: str) -> OTPCode:
        if not user.is_active:
            raise PermissionDenied("User account is inactive.")

        otp = (
            OTPCode.objects.select_for_update()
            .filter(user=user, is_used=False)
            .order_by("-created_at")
            .first()
        )

        if otp is None:
            raise ValidationError({"code": "Invalid or expired verification code."})

        if otp.is_expired:
            otp.is_used = True
            otp.save(update_fields=["is_used"])
            raise ValidationError({"code": "Invalid or expired verification code."})

        if not otp.verify_code(code):
            raise ValidationError({"code": "Invalid or expired verification code."})

        otp.is_used = True
        otp.save(update_fields=["is_used"])

        if not user.is_verified:
            user.is_verified = True
            user.save(update_fields=["is_verified"])

        return otp

    def _enforce_rate_limit(self, user: User) -> None:
        window_start = timezone.now() - self.rate_limit_window
        recent_requests = OTPCode.objects.filter(
            user=user,
            created_at__gte=window_start,
        ).count()
        if recent_requests >= self.max_requests_per_window:
            raise ValidationError(
                {"phone_number": "Too many OTP requests. Please try again later."}
            )
