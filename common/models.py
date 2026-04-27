import uuid

from django.conf import settings
from django.db import models


class TimestampedUUIDModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Notification(TimestampedUUIDModel):
    class NotificationType(models.TextChoices):
        EMERGENCY = "emergency", "Emergency"
        DISPATCH = "dispatch", "Dispatch"
        STATUS = "status", "Status"
        SYSTEM = "system", "System"
        VERIFICATION = "verification", "Verification"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    notification_type = models.CharField(
        max_length=32,
        choices=NotificationType.choices,
        default=NotificationType.SYSTEM,
    )
    title = models.CharField(max_length=255)
    message = models.TextField()
    data = models.JSONField(default=dict, blank=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Notification<{self.notification_type} to {self.user_id}>"
