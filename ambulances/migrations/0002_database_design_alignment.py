import django.contrib.gis.db.models.fields
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("ambulances", "0001_initial"),
    ]

    operations = [
        migrations.RenameField(
            model_name="ambulance",
            old_name="code",
            new_name="plate_number",
        ),
        migrations.AddField(
            model_name="ambulance",
            name="ambulance_type",
            field=models.CharField(
                choices=[
                    ("basic", "Basic"),
                    ("advanced", "Advanced"),
                    ("icu_mobile", "ICU Mobile"),
                    ("neonatal", "Neonatal"),
                    ("patient_transport", "Patient Transport"),
                ],
                default="basic",
                max_length=32,
            ),
        ),
        migrations.AddField(
            model_name="ambulance",
            name="current_location",
            field=django.contrib.gis.db.models.fields.PointField(blank=True, null=True, srid=4326),
        ),
        migrations.AddField(
            model_name="ambulance",
            name="equipment",
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name="ambulance",
            name="image",
            field=models.FileField(blank=True, null=True, upload_to="ambulances/images/"),
        ),
        migrations.AddField(
            model_name="ambulance",
            name="last_location_update",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="ambulance",
            name="organization",
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name="ambulance",
            name="phone",
            field=models.CharField(blank=True, max_length=32),
        ),
        migrations.AddField(
            model_name="ambulance",
            name="vehicle_color",
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AddField(
            model_name="ambulance",
            name="vehicle_model",
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name="ambulance",
            name="vehicle_year",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="ambulance",
            name="verification_status",
            field=models.CharField(
                choices=[("pending", "Pending"), ("approved", "Approved"), ("rejected", "Rejected")],
                default="pending",
                max_length=16,
            ),
        ),
        migrations.AddField(
            model_name="ambulance",
            name="verified_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="ambulance",
            name="verified_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="verified_ambulances",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name="ambulance",
            name="driver",
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="ambulance_profile",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name="ambulance",
            name="status",
            field=models.CharField(
                choices=[
                    ("available", "Available"),
                    ("en_route", "En Route"),
                    ("busy", "Busy"),
                    ("offline", "Offline"),
                    ("on_duty", "On Duty"),
                    ("maintenance", "Maintenance"),
                ],
                default="available",
                max_length=32,
            ),
        ),
        migrations.RemoveField(
            model_name="ambulance",
            name="is_active",
        ),
    ]
