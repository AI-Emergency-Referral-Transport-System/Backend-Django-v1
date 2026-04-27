from django.conf import settings
from django.db import models
from common.models import TimestampedUUIDModel


class Ambulance(TimestampedUUIDModel):
    class Status(models.TextChoices):
        AVAILABLE = "available", "Available"
        EN_ROUTE = "en_route", "En Route"
        BUSY = "busy", "Busy"
        OFFLINE = "offline", "Offline"

    plate_number = models.CharField(max_length=20, unique=True)
    driver = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="ambulance_profile",
        null=True,
        blank=True,
    )
    hospital = models.ForeignKey(
        "hospitals.Hospital",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ambulances",
    )

    organization = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=32, blank=True)
    equipment = models.JSONField(default=list, blank=True)

    if settings.GIS_ENABLED:
        current_location = models.PointField(srid=4326, null=True, blank=True)
        last_location_update = models.DateTimeField(null=True, blank=True)

    status = models.CharField(
        max_length=32,
        choices=Status.choices,
        default=Status.AVAILABLE
    )

    class Meta:
        ordering = ["plate_number"]

    def __str__(self) -> str:
        return f"{self.plate_number} ({self.status})"


if settings.GIS_ENABLED:
    class LocationTrack(TimestampedUUIDModel):
        ambulance = models.ForeignKey(
            Ambulance, on_delete=models.CASCADE, related_name="location_tracks"
        )
        location = models.PointField(srid=4326)
        timestamp = models.DateTimeField(auto_now_add=True)

        class Meta:
            ordering = ["-timestamp"]


class Driver(TimestampedUUIDModel):
    class Availability(models.TextChoices):
        ONLINE = "online", "Online"
        OFFLINE = "offline", "Offline"

    class VerificationStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="driver_profile",
        limit_choices_to={"role": "driver"},
    )
    ambulance = models.ForeignKey(
        Ambulance,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="drivers",
    )
    license_number = models.CharField(max_length=50, blank=True)
    license_expiry = models.DateField(null=True, blank=True)
    experience_years = models.IntegerField(default=0)
    availability = models.CharField(
        max_length=16,
        choices=Availability.choices,
        default=Availability.OFFLINE,
    )
    verification_status = models.CharField(
        max_length=16,
        choices=VerificationStatus.choices,
        default=VerificationStatus.PENDING,
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Driver: {self.user.email}"