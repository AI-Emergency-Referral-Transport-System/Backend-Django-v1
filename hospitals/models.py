from django.conf import settings
from django.contrib.gis.db import models

from common.models import TimestampedUUIDModel


class Hospital(TimestampedUUIDModel):
    class FacilityType(models.TextChoices):
        HOSPITAL = "hospital", "Hospital"
        CLINIC = "clinic", "Clinic"
        HEALTH_CENTER = "health_center", "Health Center"
        SPECIALIZED = "specialized", "Specialized"

    class OxygenLevel(models.TextChoices):
        HIGH = "high", "High"
        MEDIUM = "medium", "Medium"
        LOW = "low", "Low"
        CRITICAL = "critical", "Critical"

    class VerificationStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    name = models.CharField(max_length=255)
    facility_type = models.CharField(
        max_length=32,
        choices=FacilityType.choices,
        default=FacilityType.HOSPITAL,
    )
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    region = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    website = models.URLField(blank=True)
    landmark = models.CharField(max_length=255, blank=True)
    registration_number = models.CharField(max_length=100, unique=True, null=True, blank=True)
    description = models.TextField(blank=True)
    specialties = models.JSONField(default=list, blank=True)
    services = models.JSONField(default=list, blank=True)
    departments = models.JSONField(default=list, blank=True)
    admin = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="managed_hospital",
        limit_choices_to={"role": "hospital_admin"},
    )
    location = models.PointField(geography=True, srid=4326)

    total_beds = models.PositiveIntegerField(default=100)
    available_beds = models.PositiveIntegerField(default=0)
    occupied_beds = models.PositiveIntegerField(default=0)
    total_icu_beds = models.PositiveIntegerField(default=10)
    available_icu_beds = models.PositiveIntegerField(default=0)
    occupied_icu_beds = models.PositiveIntegerField(default=0)
    oxygen_level = models.CharField(
        max_length=16,
        choices=OxygenLevel.choices,
        default=OxygenLevel.HIGH,
    )
    has_oxygen = models.BooleanField(default=True)
    oxygen_units = models.PositiveIntegerField(default=20)
    has_ventilator = models.BooleanField(default=False)
    ventilator_units = models.PositiveIntegerField(default=0)

    has_emergency = models.BooleanField(default=True)
    has_icu = models.BooleanField(default=False)
    has_surgery = models.BooleanField(default=False)
    has_cardiology = models.BooleanField(default=False)
    has_trauma = models.BooleanField(default=False)
    has_maternity = models.BooleanField(default=False)
    has_neonatal = models.BooleanField(default=False)
    has_ambulance = models.BooleanField(default=True)

    operating_hours = models.JSONField(default=dict, blank=True)
    working_hours = models.JSONField(default=dict, blank=True)
    rating = models.FloatField(default=4.5)
    total_reviews = models.PositiveIntegerField(default=0)
    image = models.FileField(upload_to="hospitals/images/", blank=True, null=True)
    logo = models.FileField(upload_to="hospitals/logos/", blank=True, null=True)
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
        related_name="verified_hospitals",
    )
    verified_at = models.DateTimeField(null=True, blank=True)

    is_available = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class HospitalResourceLog(TimestampedUUIDModel):
    class Action(models.TextChoices):
        RESERVED = "reserved", "Reserved"
        RELEASED = "released", "Released"
        UPDATED = "updated", "Updated"

    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE, related_name="resource_logs")
    resource_type = models.CharField(max_length=32)
    quantity_change = models.IntegerField(default=0)
    previous_value = models.IntegerField(default=0)
    new_value = models.IntegerField(default=0)
    action = models.CharField(max_length=16, choices=Action.choices, default=Action.UPDATED)
    emergency = models.ForeignKey(
        "emergencies.Emergency",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="hospital_resource_logs",
    )
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"HospitalResourceLog<{self.resource_type} for {self.hospital_id}>"


class HospitalAlert(TimestampedUUIDModel):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ACKNOWLEDGED = "acknowledged", "Acknowledged"
        PREPARING = "preparing", "Preparing"
        READY = "ready", "Ready"
        DECLINED = "declined", "Declined"
        TIMEOUT = "timeout", "Timeout"

    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE, related_name="alerts")
    emergency = models.ForeignKey(
        "emergencies.Emergency",
        on_delete=models.CASCADE,
        related_name="hospital_alerts",
    )
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    eta_minutes = models.PositiveIntegerField(null=True, blank=True)
    required_resources = models.JSONField(default=dict, blank=True)
    preparation_notes = models.TextField(blank=True)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"HospitalAlert<{self.hospital_id} for {self.emergency_id}>"
