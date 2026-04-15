from django.conf import settings
from django.db import models

from common.models import TimestampedUUIDModel


class LocationUpdate(TimestampedUUIDModel):
    ambulance = models.ForeignKey(
        "ambulances.Ambulance",
        on_delete=models.CASCADE,
        related_name="location_updates",
    )
    reported_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reported_locations",
        limit_choices_to={"role": "driver"},
    )
    #location = models.PointField(geography=True, srid=4326)
    requested_location = models.TextField(null=True, blank=True)
    heading = models.FloatField(null=True, blank=True)
    speed = models.FloatField(null=True, blank=True)
    recorded_at = models.DateTimeField()

    class Meta:
        ordering = ["-recorded_at"]

    def __str__(self) -> str:
        return f"{self.ambulance_id} @ {self.recorded_at.isoformat()}"
