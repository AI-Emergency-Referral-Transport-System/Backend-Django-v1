import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("hospitals", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Ambulance",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("code", models.CharField(max_length=64, unique=True)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("available", "Available"),
                            ("dispatched", "Dispatched"),
                            ("offline", "Offline"),
                        ],
                        default="available",
                        max_length=32,
                    ),
                ),
                ("is_active", models.BooleanField(default=True)),
                (
                    "driver",
                    models.OneToOneField(
                        blank=True,
                        limit_choices_to={"role": "driver"},
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="assigned_ambulance",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "hospital",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="ambulances",
                        to="hospitals.hospital",
                    ),
                ),
            ],
            options={
                "ordering": ["code"],
            },
        ),
    ]
