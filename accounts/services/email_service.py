from django.conf import settings
from django.core.mail import send_mail


def send_otp_email(email: str, code: str) -> None:
    send_mail(
        subject="Your verification code",
        message=f"Your verification code is: {code}. It expires in 5 minutes.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        fail_silently=False,
    )
