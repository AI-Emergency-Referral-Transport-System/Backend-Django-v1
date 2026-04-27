from django.contrib.gis.db import models
from django.conf import settings
from django.utils import timezone

from common.models import TimestampedUUIDModel


class Emergency(TimestampedUUIDModel):
    class Status(models.TextChoices):
        REQUESTED = "requested", "Requested"
        DRIVER_ASSIGNED = "driver_assigned", "Driver Assigned"
        DRIVER_GOING_TO_PATIENT = "driver_going_to_patient", "Driver Going to Patient"
        DRIVER_ARRIVED = "driver_arrived", "Driver Arrived"
        GOING_TO_HOSPITAL = "going_to_hospital", "Going to Hospital"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"
        PENDING = 'pending', 'Searching for Ambulance'
        ACCEPTED = 'accepted', 'Ambulance En Route'
        RETRIEVED = 'retrieved', 'Patient picked up'
        DELIVERED = 'delivered', 'Patient delivered to hospital'

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
    assigned_ambulance = models.ForeignKey(
        "ambulances.Ambulance",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="emergencies",
    )
    selected_hospital = models.ForeignKey(
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
    patient_location = models.PointField(geography=True, srid=4326, null=True, blank=True)

    # Patient-supplied description sent to AI engine
    patient_description = models.TextField(blank=True)
    description = models.TextField(blank=True)
    summary = models.TextField(blank=True)
    pickup_latitude = models.FloatField(null=True, blank=True)
    pickup_longitude = models.FloatField(null=True, blank=True)
    pickup_address = models.TextField(blank=True)
    destination_latitude = models.FloatField(null=True, blank=True)
    destination_longitude = models.FloatField(null=True, blank=True)
    patient_name = models.CharField(max_length=255, blank=True)
    patient_age = models.PositiveIntegerField(null=True, blank=True)
    patient_condition = models.TextField(blank=True)
    patient_phone = models.CharField(max_length=32, blank=True)
    patient_blood_type = models.CharField(max_length=5, blank=True)
    patient_allergies = models.TextField(blank=True)
    ai_generated = models.BooleanField(default=False)
    ai_raw_input = models.TextField(blank=True)
    conversation_id = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)
    estimated_arrival_minutes = models.PositiveIntegerField(null=True, blank=True)
    eta_minutes = models.PositiveIntegerField(null=True, blank=True)
    distance_km = models.FloatField(null=True, blank=True)
    is_resolved = models.BooleanField(default=False)
    dispatched_at = models.DateTimeField(null=True, blank=True)

    completed_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.patient_id} | {self.emergency_type} | {self.status}"

    @property
    def ambulance(self):
        return self.assigned_ambulance

    @ambulance.setter
    def ambulance(self, value):
        self.assigned_ambulance = value

    @property
    def hospital(self):
        return self.selected_hospital

    @hospital.setter
    def hospital(self, value):
        self.selected_hospital = value

    @property
    def requested_location(self):
        return self.patient_location

    def save(self, *args, **kwargs):
        if self.patient_location:
            self.pickup_longitude = self.patient_location.x
            self.pickup_latitude = self.patient_location.y
        if self.selected_hospital and self.selected_hospital.location:
            self.destination_longitude = self.selected_hospital.location.x
            self.destination_latitude = self.selected_hospital.location.y
        if self.patient:
            self.patient_name = self.patient_name or self.patient.full_name
            self.patient_phone = self.patient_phone or (self.patient.phone_number or "")
            self.patient_blood_type = self.patient_blood_type or self.patient.blood_type
            self.patient_allergies = self.patient_allergies or self.patient.allergies
            if self.patient_age is None:
                self.patient_age = self.patient.age
        super().save(*args, **kwargs)

    def mark_completed(self):
        self.status = self.Status.COMPLETED
        self.is_resolved = True
        self.completed_at = timezone.now()
        self.save(update_fields=["status", "is_resolved", "completed_at", "updated_at"])


class EmergencyStatusLog(TimestampedUUIDModel):
    emergency = models.ForeignKey(Emergency, on_delete=models.CASCADE, related_name="status_logs")
    status = models.CharField(max_length=64)
    message = models.TextField(blank=True)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="emergency_status_changes",
    )
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"EmergencyStatusLog<{self.emergency_id}:{self.status}>"


class HospitalSuggestion(TimestampedUUIDModel):
    emergency = models.ForeignKey(Emergency, on_delete=models.CASCADE, related_name="hospital_suggestions")
    hospital = models.ForeignKey(
        "hospitals.Hospital",
        on_delete=models.CASCADE,
        related_name="emergency_suggestions",
    )
    distance_km = models.FloatField(null=True, blank=True)
    score = models.FloatField(default=0.0)
    reason = models.TextField(blank=True)
    is_selected = models.BooleanField(default=False)

    class Meta:
        ordering = ["-score", "distance_km"]

    def __str__(self) -> str:
        return f"HospitalSuggestion<{self.hospital_id} for {self.emergency_id}>"
