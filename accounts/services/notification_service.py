from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.mail import send_mail
from rest_framework.exceptions import ValidationError

from accounts.services.sms_service import send_sms


def _print_otp(phone_number: str, otp_code: str) -> None:
    print(f"[OTP DEBUG] {phone_number}: {otp_code}")


def send_otp_notification(user, otp_code: str) -> None:
    backend = getattr(settings, "OTP_DELIVERY_BACKEND", "console").strip().lower()
    message = f"Your verification code is: {otp_code}. It expires in 5 minutes."

    if backend == "console":
        _print_otp(user.phone_number, otp_code)
        return

    if backend == "sms":
        if not user.phone_number:
            raise ValidationError({"phone_number": "Phone number is required for SMS OTP delivery."})
        send_sms(phone_number=user.phone_number, message=message)
        if getattr(settings, "OTP_DEBUG_OUTPUT", False):
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
        if getattr(settings, "OTP_DEBUG_OUTPUT", False):
            _print_otp(user.phone_number, otp_code)
        return

    raise ImproperlyConfigured(
        "Unsupported OTP_DELIVERY_BACKEND. Use one of: console, sms, email."
    )
