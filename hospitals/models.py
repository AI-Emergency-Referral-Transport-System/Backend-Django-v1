from django.conf import settings
from django.contrib.gis.db import models

from common.models import TimestampedUUIDModel


class Hospital(TimestampedUUIDModel):
    class OxygenLevel(models.TextChoices):
        HIGH = "high", "High"
        MEDIUM = "medium", "Medium"
        LOW = "low", "Low"
        CRITICAL = "critical", "Critical"

    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20, blank=True)
    admin = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="managed_hospital",
        limit_choices_to={"role": "hospital_admin"},
    )
    location = models.PointField(geography=True, srid=4326)

    
    available_beds = models.PositiveIntegerField(default=0)
    available_icu_beds = models.PositiveIntegerField(default=0)
    oxygen_level = models.CharField(
        max_length=16,
        choices=OxygenLevel.choices,
        default=OxygenLevel.HIGH,
    )

    # Specialties
    has_cardiology = models.BooleanField(default=False)
    has_trauma = models.BooleanField(default=False)

    is_available = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name
