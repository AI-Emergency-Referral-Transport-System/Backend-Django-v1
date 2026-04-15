from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone
from accounts.managers import UserManager
from common.models import TimestampedUUIDModel

class User(TimestampedUUIDModel, AbstractBaseUser, PermissionsMixin):
    class Role(models.TextChoices):
        PATIENT = "patient", "Patient"
        DRIVER = "driver", "Driver"
        HOSPITAL_ADMIN = "hospital_admin", "Hospital Admin"

    phone_number = models.CharField(max_length=32, unique=True)
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    role = models.CharField(max_length=32, choices=Role.choices, default=Role.PATIENT)
    
    # Medical Data (Required by AI for hospital matching)
    blood_type = models.CharField(max_length=5, blank=True, null=True)
    allergies = models.TextField(blank=True, null=True)
    medical_history = models.TextField(blank=True, null=True)
    emergency_contacts = models.JSONField(default=list, blank=True)
    preferred_language = models.CharField(max_length=10, default='en')

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    USERNAME_FIELD = "phone_number"
    REQUIRED_FIELDS: list[str] = []

    objects = UserManager()

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.phone_number} ({self.role})"


class OTPCode(TimestampedUUIDModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="otp_codes")
    code = models.CharField(max_length=6)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]

    @property
    def is_expired(self) -> bool:
        return timezone.now() >= self.expires_at