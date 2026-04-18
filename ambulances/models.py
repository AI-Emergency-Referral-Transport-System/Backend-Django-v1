from django.conf import settings
from django.contrib.gis.db import models
from common.models import TimestampedUUIDModel

class Ambulance(TimestampedUUIDModel):
    class Status(models.TextChoices):
        AVAILABLE = "available", "Available"
        EN_ROUTE = "en_route", "En Route"
        BUSY = "busy", "Busy"
        OFFLINE = "offline", "Offline"

    class VehicleType(models.TextChoices):
        BASIC = "basic", "Basic"
        ADVANCED = "advanced", "Advanced"
        NEONATAL = "neonatal", "Neonatal"

    plate_number = models.CharField(max_length=20, unique=True) 
    vehicle_type = models.CharField(
        max_length=20, 
        choices=VehicleType.choices, 
        default=VehicleType.BASIC
    )

    driver = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="ambulance_profile",
    )
    hospital = models.ForeignKey(
        "hospitals.Hospital",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ambulances",
    )

    current_location = models.PointField(srid=4326)
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