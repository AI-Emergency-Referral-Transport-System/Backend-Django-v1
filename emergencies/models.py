from django.contrib.gis.db import models
from django.conf import settings
from django.utils import timezone

from common.models import TimestampedUUIDModel


class Emergency(TimestampedUUIDModel):
    class Status(models.TextChoices):
        REQUESTED = "requested", "Requested"
        ASSIGNED = "assigned", "Assigned"
        IN_PROGRESS = "in_progress", "In Progress"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    class Priority(models.TextChoices):
        CRITICAL = "critical", "Critical"
        HIGH = "high", "High"
        MEDIUM = "medium", "Medium"
        LOW = "low", "Low"

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

    emergency_type = models.CharField(max_length=64, blank=True, help_text="e.g. cardiac, trauma, accident")
    priority = models.CharField(
        max_length=16,
        choices=Priority.choices,
        default=Priority.MEDIUM,
    )
    status = models.CharField(
        max_length=32,
        choices=Status.choices,
        default=Status.REQUESTED,
    )

    # Patient location at time of request (GeoDjango PointField for spatial queries)
    requested_location = models.PointField(geography=True, srid=4326, null=True, blank=True)

    # Patient-supplied description sent to AI engine
    patient_description = models.TextField(blank=True)

    # Ongoing notes by drivers/hospital admins
    notes = models.TextField(blank=True)

    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.patient_id} | {self.emergency_type} | {self.status}"

    def mark_completed(self):
        self.status = self.Status.COMPLETED
        self.completed_at = timezone.now()
        self.save(update_fields=["status", "completed_at"])
