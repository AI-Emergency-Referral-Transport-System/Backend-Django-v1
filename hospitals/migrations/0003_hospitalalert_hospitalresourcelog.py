import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("emergencies", "0002_database_design_alignment"),
        ("hospitals", "0002_database_design_alignment"),
    ]

    operations = [
        migrations.CreateModel(
            name="HospitalAlert",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending"),
                            ("acknowledged", "Acknowledged"),
                            ("preparing", "Preparing"),
                            ("ready", "Ready"),
                            ("declined", "Declined"),
                            ("timeout", "Timeout"),
                        ],
                        default="pending",
                        max_length=16,
                    ),
                ),
                ("eta_minutes", models.PositiveIntegerField(blank=True, null=True)),
                ("required_resources", models.JSONField(blank=True, default=dict)),
                ("preparation_notes", models.TextField(blank=True)),
                ("acknowledged_at", models.DateTimeField(blank=True, null=True)),
                ("expires_at", models.DateTimeField(blank=True, null=True)),
                (
                    "emergency",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="hospital_alerts",
                        to="emergencies.emergency",
                    ),
                ),
                (
                    "hospital",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="alerts",
                        to="hospitals.hospital",
                    ),
                ),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="HospitalResourceLog",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("resource_type", models.CharField(max_length=32)),
                ("quantity_change", models.IntegerField(default=0)),
                ("previous_value", models.IntegerField(default=0)),
                ("new_value", models.IntegerField(default=0)),
                (
                    "action",
                    models.CharField(
                        choices=[
                            ("reserved", "Reserved"),
                            ("released", "Released"),
                            ("updated", "Updated"),
                        ],
                        default="updated",
                        max_length=16,
                    ),
                ),
                ("notes", models.TextField(blank=True)),
                (
                    "emergency",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="hospital_resource_logs",
                        to="emergencies.emergency",
                    ),
                ),
                (
                    "hospital",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="resource_logs",
                        to="hospitals.hospital",
                    ),
                ),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
    ]
