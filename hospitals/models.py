from django.conf import settings
from django.db import models

from common.models import TimestampedUUIDModel


class Hospital(TimestampedUUIDModel):
    name = models.CharField(max_length=255)
    admin = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="managed_hospital",
        limit_choices_to={"role": "hospital_admin"},
    )
    #location = models.PointField(geography=True, srid=4326)
    requested_location = models.TextField(null=True, blank=True)
    capacity_total = models.PositiveIntegerField(default=0)
    capacity_available = models.PositiveIntegerField(default=0)
    is_available = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name
