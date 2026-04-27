import django.contrib.gis.db.models.fields
import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("ambulances", "0002_database_design_alignment"),
        ("emergencies", "0002_database_design_alignment"),
    ]

    operations = [
        migrations.CreateModel(
            name="Location_Track",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("coordinates", django.contrib.gis.db.models.fields.PointField(srid=4326)),
                ("speed", models.FloatField(blank=True, null=True)),
                ("heading", models.FloatField(blank=True, null=True)),
                ("accuracy", models.FloatField(blank=True, null=True)),
                ("timestamp", models.DateTimeField(auto_now_add=True)),
                (
                    "ambulance",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="ambulances.ambulance"),
                ),
                (
                    "emergency",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="location_history",
                        to="emergencies.emergency",
                    ),
                ),
            ],
            options={
                "ordering": ["-timestamp"],
            },
        ),
        migrations.CreateModel(
            name="RoutePoint",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("latitude", models.FloatField()),
                ("longitude", models.FloatField()),
                ("sequence", models.PositiveIntegerField(default=0)),
                ("timestamp", models.DateTimeField(auto_now_add=True)),
                (
                    "emergency",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="route_points",
                        to="emergencies.emergency",
                    ),
                ),
            ],
            options={
                "ordering": ["sequence", "timestamp"],
            },
        ),
    ]
