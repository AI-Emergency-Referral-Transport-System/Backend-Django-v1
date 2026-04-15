from django.db import models
from django.conf import settings

from common.models import TimestampedUUIDModel


class Emergency(TimestampedUUIDModel):
    class Status(models.TextChoices):
        REQUESTED = "requested", "Requested"
        ASSIGNED = "assigned", "Assigned"
        IN_PROGRESS = "in_progress", "In Progress"
        COMPLETED = "completed", "Completed"

    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="emergencies",
        limit_choices_to={"role": "patient"},
    )
    ambulance = models.ForeignKey(
        "ambulances.Ambulance",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="emergencies",
    )
    hospital = models.ForeignKey(
        "hospitals.Hospital",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="emergencies",
    )
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.REQUESTED)
    #requested_location = models.PointField(geography=True, srid=4326, null=True, blank=True)
    requested_location = models.TextField(null=True, blank=True)
    summary = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.patient_id} - {self.status}"
