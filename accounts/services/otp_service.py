import secrets
from datetime import timedelta

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError

from accounts.models import OTPCode, User
from accounts.services.email_service import send_otp_email


class OTPService:
    expiry_window = timedelta(minutes=5)
    rate_limit_window = timedelta(minutes=10)
    max_requests_per_window = 5

    def request_otp(self, user: User) -> OTPCode:
        if not user.is_active:
            raise PermissionDenied("User account is inactive.")
        if not user.email:
            raise ValidationError({"email": "A verified email address is required."})

        self._enforce_rate_limit(user)
        OTPCode.objects.filter(user=user, is_used=False).update(is_used=True)

        raw_code = f"{secrets.randbelow(10**6):06d}"
        otp = OTPCode(
            user=user,
            expires_at=timezone.now() + self.expiry_window,
        )
        otp.set_code(raw_code)
        otp.save()

        send_otp_email(email=user.email, code=raw_code)

        user.last_otp_sent = timezone.now()
        user.save(update_fields=["last_otp_sent"])

        return otp

    @transaction.atomic
    def verify_otp(self, user: User, code: str) -> bool:
        if not user.is_active:
            raise PermissionDenied("User account is inactive.")

        otp = (
            OTPCode.objects.select_for_update()
            .filter(user=user, is_used=False)
            .order_by("-created_at")
            .first()
        )

        if otp is None or otp.is_expired:
            if otp:
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

        return True

    def _enforce_rate_limit(self, user: User) -> None:
        window_start = timezone.now() - self.rate_limit_window
        recent_requests = OTPCode.objects.filter(
            user=user,
            created_at__gte=window_start,
        ).count()

        if recent_requests >= self.max_requests_per_window:
            raise ValidationError(
                {"email": "Too many OTP requests. Please try again later."}
            )
