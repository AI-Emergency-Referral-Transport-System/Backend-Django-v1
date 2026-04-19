import django.contrib.gis.db.models.fields
import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("ambulances", "0001_initial"),
        ("hospitals", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Emergency",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "emergency_type",
                    models.CharField(blank=True, help_text="e.g. cardiac, trauma, accident", max_length=64),
                ),
                (
                    "priority",
                    models.CharField(
                        choices=[
                            ("critical", "Critical"),
                            ("high", "High"),
                            ("medium", "Medium"),
                            ("low", "Low"),
                        ],
                        default="medium",
                        max_length=16,
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("requested", "Requested"),
                            ("assigned", "Assigned"),
                            ("in_progress", "In Progress"),
                            ("completed", "Completed"),
                            ("cancelled", "Cancelled"),
                        ],
                        default="requested",
                        max_length=32,
                    ),
                ),
                (
                    "requested_location",
                    django.contrib.gis.db.models.fields.PointField(blank=True, geography=True, null=True, srid=4326),
                ),
                ("patient_description", models.TextField(blank=True)),
                ("notes", models.TextField(blank=True)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                (
                    "ambulance",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="emergencies",
                        to="ambulances.ambulance",
                    ),
                ),
                (
                    "hospital",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="emergencies",
                        to="hospitals.hospital",
                    ),
                ),
                (
                    "patient",
                    models.ForeignKey(
                        limit_choices_to={"role": "patient"},
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="emergencies",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
    ]
