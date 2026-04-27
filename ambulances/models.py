from django.conf import settings
from django.contrib.gis.db import models
from common.models import TimestampedUUIDModel


class Ambulance(TimestampedUUIDModel):
    class AmbulanceType(models.TextChoices):
        BASIC = "basic", "Basic"
        ADVANCED = "advanced", "Advanced"
        ICU_MOBILE = "icu_mobile", "ICU Mobile"
        NEONATAL = "neonatal", "Neonatal"
        PATIENT_TRANSPORT = "patient_transport", "Patient Transport"

    class Status(models.TextChoices):
        AVAILABLE = "available", "Available"
        EN_ROUTE = "en_route", "En Route"
        BUSY = "busy", "Busy"
        OFFLINE = "offline", "Offline"
        ON_DUTY = "on_duty", "On Duty"
        MAINTENANCE = "maintenance", "Maintenance"

    class VerificationStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    plate_number = models.CharField(max_length=20, unique=True)
    ambulance_type = models.CharField(
        max_length=32,
        choices=AmbulanceType.choices,
        default=AmbulanceType.BASIC,
    )
    vehicle_model = models.CharField(max_length=100, blank=True)
    vehicle_year = models.PositiveIntegerField(null=True, blank=True)
    vehicle_color = models.CharField(max_length=50, blank=True)
    driver = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ambulance_profile",
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
    image = models.FileField(upload_to="ambulances/images/", blank=True, null=True)

    status = models.CharField(
        max_length=32,
        choices=Status.choices,
        default=Status.AVAILABLE
    )
    verification_status = models.CharField(
        max_length=16,
        choices=VerificationStatus.choices,
        default=VerificationStatus.PENDING,
    )
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="verified_ambulances",
    )
    verified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["plate_number"]

    def __str__(self) -> str:
        return f"{self.plate_number} ({self.status})"
