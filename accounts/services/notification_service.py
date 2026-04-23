import os

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.mail import send_mail
from rest_framework.exceptions import ValidationError

from accounts.services.sms_service import send_sms


def _print_otp(phone_number: str, otp_code: str) -> None:
    print(f"[OTP DEBUG] {phone_number}: {otp_code}")


def _string_setting(name: str, default: str = "") -> str:
    value = getattr(settings, name, None)
    if value in (None, ""):
        value = os.getenv(name, default)
    return value


def _bool_setting(name: str, default: bool = False) -> bool:
    value = getattr(settings, name, None)
    if value is None:
        raw = os.getenv(name)
        if raw is None:
            return default
        return raw.strip().lower() == "true"
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() == "true"


def send_otp_notification(user, otp_code: str) -> None:
    configured_backend = _string_setting("OTP_DELIVERY_BACKEND", "").strip().lower()
    if configured_backend:
        backend = configured_backend
    else:
        backend = "sms" if _string_setting("SMS_PROVIDER", "").strip() else "console"

    message = f"Your verification code is: {otp_code}. It expires in 5 minutes."

    if backend == "console":
        _print_otp(user.phone_number, otp_code)
        return

    if backend == "sms":
        if not user.phone_number:
            raise ValidationError({"phone_number": "Phone number is required for SMS OTP delivery."})
        send_sms(phone_number=user.phone_number, message=message)
        if _bool_setting("OTP_DEBUG_OUTPUT", False):
            _print_otp(user.phone_number, otp_code)
        return

    if backend == "email":
        if not user.email:
            raise ValidationError({"email": "Email is required for email OTP delivery."})
        send_mail(
            subject="Your verification code",
            message=message,
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@example.com"),
            recipient_list=[user.email],
            fail_silently=False,
        )
        if _bool_setting("OTP_DEBUG_OUTPUT", False):
            _print_otp(user.phone_number, otp_code)
        return

    raise ImproperlyConfigured(
        "Unsupported OTP_DELIVERY_BACKEND. Use one of: console, sms, email."
    )
