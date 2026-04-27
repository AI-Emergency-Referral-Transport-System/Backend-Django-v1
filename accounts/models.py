from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.utils import timezone
from datetime import timedelta

from accounts.managers import UserManager
from common.models import TimestampedUUIDModel

class User(TimestampedUUIDModel, AbstractBaseUser, PermissionsMixin):
    class Role(models.TextChoices):
        PATIENT = "patient", "Patient"
        DRIVER = "driver", "Driver"
        HOSPITAL_ADMIN = "hospital_admin", "Hospital Admin"

    phone_number = models.CharField(max_length=32, unique=True, null=True, blank=True)
    email = models.EmailField(unique=True, null=True, blank=True)
    role = models.CharField(max_length=32, choices=Role.choices, default=Role.PATIENT)
    is_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    # Useful for rate-limiting OTP delivery
    last_otp_sent = models.DateTimeField(null=True, blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: list[str] = []

    objects = UserManager()

    class Meta:
        ordering = ["-date_joined"]

    def __str__(self) -> str:
        return f"{self.email or self.phone_number or self.pk} ({self.role})"

    @property
    def safe_driver_profile(self):
        try:
            return self.driver_profile
        except ObjectDoesNotExist:
            return None

    @property
    def safe_hospital_profile(self):
        try:
            return self.hospital_profile
        except ObjectDoesNotExist:
            return None

    def get_authorization_status(self) -> str:
        if self.role == self.Role.DRIVER:
            driver_profile = self.safe_driver_profile
            if driver_profile is None:
                return DriverProfile.VerificationStatus.PENDING
            return driver_profile.verification_status

        if self.role == self.Role.HOSPITAL_ADMIN:
            hospital_profile = self.safe_hospital_profile
            if hospital_profile is None:
                return HospitalProfile.RegistrationStatus.PENDING
            return hospital_profile.registration_status

        return "approved" if self.is_verified else "pending"

    def is_authorization_completed(self) -> bool:
        return self.get_authorization_status() == "approved"


class Profile(TimestampedUUIDModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    full_name = models.CharField(max_length=255, blank=True)
    emergency_contact = models.CharField(max_length=32, blank=True)
    blood_type = models.CharField(max_length=5, blank=True)
    location = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["user__phone_number"]

    def __str__(self) -> str:
        return f"Profile<{self.user.email or self.user.phone_number or self.user_id}>"

    @property
    def driver_profile(self):
        return self.user.safe_driver_profile

    @property
    def hospital_profile(self):
        return self.user.safe_hospital_profile


class DriverProfile(TimestampedUUIDModel):
    class Availability(models.TextChoices):
        ONLINE = "online", "Online"
        OFFLINE = "offline", "Offline"

    class VerificationStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="driver_profile",
        limit_choices_to={"role": User.Role.DRIVER},
    )
    plate_number = models.CharField(max_length=32, blank=True)
    vehicle_type = models.CharField(max_length=64, blank=True)
    availability = models.CharField(
        max_length=16,
        choices=Availability.choices,
        default=Availability.OFFLINE,
    )
    has_oxygen = models.BooleanField(default=False)
    has_defibrillator = models.BooleanField(default=False)
    verification_status = models.CharField(
        max_length=16,
        choices=VerificationStatus.choices,
        default=VerificationStatus.PENDING,
    )

    class Meta:
        ordering = ["user__phone_number"]

    def __str__(self) -> str:
        return f"DriverProfile<{self.user.phone_number}>"


class HospitalProfile(TimestampedUUIDModel):
    class RegistrationStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    class OxygenLevel(models.TextChoices):
        HIGH = "high", "High"
        MEDIUM = "medium", "Medium"
        LOW = "low", "Low"
        CRITICAL = "critical", "Critical"

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="hospital_profile",
        limit_choices_to={"role": User.Role.HOSPITAL_ADMIN},
    )
    hospital_name = models.CharField(max_length=255, blank=True)
    address = models.CharField(max_length=255, blank=True)
    available_beds = models.PositiveIntegerField(default=0)
    icu_available = models.BooleanField(default=False)
    oxygen_level = models.CharField(
        max_length=16,
        choices=OxygenLevel.choices,
        default=OxygenLevel.HIGH,
    )
    services = models.JSONField(default=list, blank=True)
    registration_status = models.CharField(
        max_length=16,
        choices=RegistrationStatus.choices,
        default=RegistrationStatus.PENDING,
    )

    class Meta:
        ordering = ["hospital_name", "user__phone_number"]

    def __str__(self) -> str:
        return f"HospitalProfile<{self.user.phone_number}>"


class OTPCode(TimestampedUUIDModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="otp_codes")
    code = models.CharField(max_length=255) # Hashed
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]

    @property
    def is_expired(self) -> bool:
        return timezone.now() >= self.expires_at

    def set_code(self, raw_code: str) -> None:
        """Hashes the OTP code before saving."""
        self.code = make_password(raw_code)

    def verify_code(self, raw_code: str) -> bool:
        """Checks raw OTP against hashed code."""
        return check_password(raw_code, self.code)


class EmergencyContact(TimestampedUUIDModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="emergency_contacts")
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=32)
    relationship = models.CharField(max_length=64, blank=True)
    is_primary = models.BooleanField(default=False)

    class Meta:
        ordering = ["-is_primary", "-created_at"]

    def __str__(self) -> str:
        return f"{self.name} ({self.phone})"
