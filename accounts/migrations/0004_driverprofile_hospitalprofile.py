import uuid

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0003_alter_user_managers"),
    ]

    operations = [
        migrations.CreateModel(
            name="DriverProfile",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("plate_number", models.CharField(blank=True, max_length=32)),
                ("vehicle_type", models.CharField(blank=True, max_length=64)),
                (
                    "availability",
                    models.CharField(
                        choices=[("online", "Online"), ("offline", "Offline")],
                        default="offline",
                        max_length=16,
                    ),
                ),
                ("has_oxygen", models.BooleanField(default=False)),
                ("has_defibrillator", models.BooleanField(default=False)),
                (
                    "verification_status",
                    models.CharField(
                        choices=[("pending", "Pending"), ("approved", "Approved"), ("rejected", "Rejected")],
                        default="pending",
                        max_length=16,
                    ),
                ),
                (
                    "user",
                    models.OneToOneField(
                        limit_choices_to={"role": "driver"},
                        on_delete=models.deletion.CASCADE,
                        related_name="driver_profile",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["user__phone_number"],
            },
        ),
        migrations.CreateModel(
            name="HospitalProfile",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("hospital_name", models.CharField(blank=True, max_length=255)),
                ("address", models.CharField(blank=True, max_length=255)),
                ("available_beds", models.PositiveIntegerField(default=0)),
                ("icu_available", models.BooleanField(default=False)),
                (
                    "oxygen_level",
                    models.CharField(
                        choices=[
                            ("high", "High"),
                            ("medium", "Medium"),
                            ("low", "Low"),
                            ("critical", "Critical"),
                        ],
                        default="high",
                        max_length=16,
                    ),
                ),
                ("services", models.JSONField(blank=True, default=list)),
                (
                    "registration_status",
                    models.CharField(
                        choices=[("pending", "Pending"), ("approved", "Approved"), ("rejected", "Rejected")],
                        default="pending",
                        max_length=16,
                    ),
                ),
                (
                    "user",
                    models.OneToOneField(
                        limit_choices_to={"role": "hospital_admin"},
                        on_delete=models.deletion.CASCADE,
                        related_name="hospital_profile",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["hospital_name", "user__phone_number"],
            },
        ),
    ]
