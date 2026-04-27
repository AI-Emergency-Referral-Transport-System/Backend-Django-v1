import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("ambulances", "0002_database_design_alignment"),
        ("emergencies", "0001_initial"),
        ("hospitals", "0002_database_design_alignment"),
    ]

    operations = [
        migrations.RenameField(
            model_name="emergency",
            old_name="ambulance",
            new_name="assigned_ambulance",
        ),
        migrations.RenameField(
            model_name="emergency",
            old_name="hospital",
            new_name="selected_hospital",
        ),
        migrations.RenameField(
            model_name="emergency",
            old_name="requested_location",
            new_name="patient_location",
        ),
        migrations.AddField(
            model_name="emergency",
            name="ai_generated",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="emergency",
            name="ai_raw_input",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="emergency",
            name="cancelled_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="emergency",
            name="conversation_id",
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name="emergency",
            name="description",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="emergency",
            name="destination_latitude",
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="emergency",
            name="destination_longitude",
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="emergency",
            name="dispatched_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="emergency",
            name="distance_km",
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="emergency",
            name="estimated_arrival_minutes",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="emergency",
            name="eta_minutes",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="emergency",
            name="is_resolved",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="emergency",
            name="patient_age",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="emergency",
            name="patient_allergies",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="emergency",
            name="patient_blood_type",
            field=models.CharField(blank=True, max_length=5),
        ),
        migrations.AddField(
            model_name="emergency",
            name="patient_condition",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="emergency",
            name="patient_name",
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name="emergency",
            name="patient_phone",
            field=models.CharField(blank=True, max_length=32),
        ),
        migrations.AddField(
            model_name="emergency",
            name="pickup_address",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="emergency",
            name="pickup_latitude",
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="emergency",
            name="pickup_longitude",
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="emergency",
            name="summary",
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name="emergency",
            name="status",
            field=models.CharField(
                choices=[
                    ("requested", "Requested"),
                    ("driver_assigned", "Driver Assigned"),
                    ("driver_going_to_patient", "Driver Going to Patient"),
                    ("driver_arrived", "Driver Arrived"),
                    ("going_to_hospital", "Going to Hospital"),
                    ("completed", "Completed"),
                    ("cancelled", "Cancelled"),
                    ("pending", "Searching for Ambulance"),
                    ("accepted", "Ambulance En Route"),
                    ("retrieved", "Patient picked up"),
                    ("delivered", "Patient delivered to hospital"),
                ],
                default="requested",
                max_length=32,
            ),
        ),
        migrations.CreateModel(
            name="EmergencyStatusLog",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("status", models.CharField(max_length=64)),
                ("message", models.TextField(blank=True)),
                ("latitude", models.FloatField(blank=True, null=True)),
                ("longitude", models.FloatField(blank=True, null=True)),
                (
                    "changed_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="emergency_status_changes",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "emergency",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="status_logs",
                        to="emergencies.emergency",
                    ),
                ),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="HospitalSuggestion",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("distance_km", models.FloatField(blank=True, null=True)),
                ("score", models.FloatField(default=0.0)),
                ("reason", models.TextField(blank=True)),
                ("is_selected", models.BooleanField(default=False)),
                (
                    "emergency",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="hospital_suggestions",
                        to="emergencies.emergency",
                    ),
                ),
                (
                    "hospital",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="emergency_suggestions",
                        to="hospitals.hospital",
                    ),
                ),
            ],
            options={
                "ordering": ["-score", "distance_km"],
            },
        ),
    ]
