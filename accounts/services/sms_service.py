import logging
import os
from abc import ABC, abstractmethod

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


logger = logging.getLogger(__name__)


def _setting(name: str, default: str = "") -> str:
    value = getattr(settings, name, None)
    if value in (None, ""):
        value = os.getenv(name, default)
    return value


class BaseSMSProvider(ABC):
    @abstractmethod
    def send_sms(self, phone_number: str, message: str) -> None:
        raise NotImplementedError


class ConsoleSMSProvider(BaseSMSProvider):
    def send_sms(self, phone_number: str, message: str) -> None:
        logger.info("SMS to %s: %s", phone_number, message)


class TwilioSMSProvider(BaseSMSProvider):
    def __init__(
        self,
        account_sid: str,
        auth_token: str,
        from_number: str = "",
        messaging_service_sid: str = "",
    ):
        self.account_sid = account_sid
        self.auth_token = auth_token
        self.from_number = from_number
        self.messaging_service_sid = messaging_service_sid

        if not self.account_sid or not self.auth_token:
            raise ImproperlyConfigured("Twilio requires TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN.")
        if not self.from_number and not self.messaging_service_sid:
            raise ImproperlyConfigured(
                "Twilio requires TWILIO_FROM_NUMBER or TWILIO_MESSAGING_SERVICE_SID."
            )

    def send_sms(self, phone_number: str, message: str) -> None:
        from twilio.rest import Client

        client = Client(self.account_sid, self.auth_token)
        payload = {
            "body": message,
            "to": phone_number,
        }
        if self.messaging_service_sid:
            payload["messaging_service_sid"] = self.messaging_service_sid
        else:
            payload["from_"] = self.from_number

        client.messages.create(**payload)


class AfricasTalkingSMSProvider(BaseSMSProvider):
    def __init__(self, username: str, api_key: str, sender_id: str = ""):
        self.username = username
        self.api_key = api_key
        self.sender_id = sender_id

        if not self.username or not self.api_key:
            raise ImproperlyConfigured(
                "Africa's Talking requires AFRICASTALKING_USERNAME and AFRICASTALKING_API_KEY."
            )

    def send_sms(self, phone_number: str, message: str) -> None:
        import africastalking

        africastalking.initialize(self.username, self.api_key)
        sms = africastalking.SMS
        sms.send(message, [phone_number], sender_id=self.sender_id or None)


class AfroMessageSMSProvider(BaseSMSProvider):
    def __init__(
        self,
        token: str,
        from_name: str = "",
        sender_id: str = "",
        callback_url: str = "",
    ):
        self.token = token
        self.from_name = from_name
        self.sender_id = sender_id
        self.callback_url = callback_url

        if not self.token:
            raise ImproperlyConfigured("AfroMessage requires AFROMESSAGE_TOKEN.")

    def send_sms(self, phone_number: str, message: str) -> None:
        try:
            from afromessage import AfroMessage
            from afromessage.models.sms_models import SendSMSRequest
        except ImportError as exc:
            raise ImproperlyConfigured(
                "AfroMessage support requires the 'afromessage' package to be installed."
            ) from exc

        client = AfroMessage(token=self.token)
        payload = {
            "to": phone_number,
            "message": message,
        }
        if self.from_name:
            payload["from_"] = self.from_name
        if self.sender_id:
            payload["sender"] = self.sender_id
        if self.callback_url:
            payload["callback"] = self.callback_url

        request = SendSMSRequest(**payload)
        client.sms.send(request)


def get_sms_provider() -> BaseSMSProvider:
    provider_name = _setting("SMS_PROVIDER", "").strip().lower()

    if provider_name == "console":
        if not settings.DEBUG:
            raise ImproperlyConfigured("Console SMS provider is only allowed in development.")
        return ConsoleSMSProvider()
    if provider_name == "twilio":
        return TwilioSMSProvider(
            account_sid=settings.TWILIO_ACCOUNT_SID,
            auth_token=settings.TWILIO_AUTH_TOKEN,
            from_number=settings.TWILIO_FROM_NUMBER,
            messaging_service_sid=settings.TWILIO_MESSAGING_SERVICE_SID,
        )
    if provider_name in {"africas_talking", "africastalking"}:
        return AfricasTalkingSMSProvider(
            username=_setting("AFRICASTALKING_USERNAME"),
            api_key=_setting("AFRICASTALKING_API_KEY") or _setting("SMS_API_KEY"),
            sender_id=_setting("AFRICASTALKING_SENDER_ID") or _setting("SMS_SENDER_ID"),
        )
    if provider_name in {"afromessage", "afro_message"}:
        return AfroMessageSMSProvider(
            token=_setting("AFROMESSAGE_TOKEN"),
            from_name=_setting("AFROMESSAGE_FROM"),
            sender_id=_setting("AFROMESSAGE_SENDER_ID") or _setting("SMS_SENDER_ID"),
            callback_url=_setting("AFROMESSAGE_CALLBACK_URL"),
        )
    if not provider_name:
        if settings.DEBUG:
            return ConsoleSMSProvider()
        raise ImproperlyConfigured("SMS_PROVIDER must be configured outside development.")

    raise ImproperlyConfigured(f"Unsupported SMS provider: {provider_name}")


def send_sms(phone_number: str, message: str) -> None:
    provider = get_sms_provider()
    provider.send_sms(phone_number=phone_number, message=message)
