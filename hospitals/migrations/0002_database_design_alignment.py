import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("hospitals", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="hospital",
            name="address",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="hospital",
            name="city",
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name="hospital",
            name="departments",
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name="hospital",
            name="description",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="hospital",
            name="email",
            field=models.EmailField(blank=True, max_length=254),
        ),
        migrations.AddField(
            model_name="hospital",
            name="facility_type",
            field=models.CharField(
                choices=[
                    ("hospital", "Hospital"),
                    ("clinic", "Clinic"),
                    ("health_center", "Health Center"),
                    ("specialized", "Specialized"),
                ],
                default="hospital",
                max_length=32,
            ),
        ),
        migrations.AddField(
            model_name="hospital",
            name="has_ambulance",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="hospital",
            name="has_emergency",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="hospital",
            name="has_icu",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="hospital",
            name="has_maternity",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="hospital",
            name="has_neonatal",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="hospital",
            name="has_oxygen",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="hospital",
            name="has_surgery",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="hospital",
            name="has_ventilator",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="hospital",
            name="image",
            field=models.FileField(blank=True, null=True, upload_to="hospitals/images/"),
        ),
        migrations.AddField(
            model_name="hospital",
            name="landmark",
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name="hospital",
            name="logo",
            field=models.FileField(blank=True, null=True, upload_to="hospitals/logos/"),
        ),
        migrations.AddField(
            model_name="hospital",
            name="occupied_beds",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="hospital",
            name="occupied_icu_beds",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="hospital",
            name="operating_hours",
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name="hospital",
            name="oxygen_units",
            field=models.PositiveIntegerField(default=20),
        ),
        migrations.AddField(
            model_name="hospital",
            name="rating",
            field=models.FloatField(default=4.5),
        ),
        migrations.AddField(
            model_name="hospital",
            name="region",
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name="hospital",
            name="registration_number",
            field=models.CharField(blank=True, max_length=100, null=True, unique=True),
        ),
        migrations.AddField(
            model_name="hospital",
            name="services",
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name="hospital",
            name="specialties",
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name="hospital",
            name="total_beds",
            field=models.PositiveIntegerField(default=100),
        ),
        migrations.AddField(
            model_name="hospital",
            name="total_icu_beds",
            field=models.PositiveIntegerField(default=10),
        ),
        migrations.AddField(
            model_name="hospital",
            name="total_reviews",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="hospital",
            name="validation_status",
            field=models.CharField(
                choices=[("pending", "Pending"), ("approved", "Approved"), ("rejected", "Rejected")],
                default="pending",
                max_length=16,
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="hospital",
            name="ventilator_units",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="hospital",
            name="verified_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="hospital",
            name="verified_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="verified_hospitals",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="hospital",
            name="website",
            field=models.URLField(blank=True),
        ),
        migrations.AddField(
            model_name="hospital",
            name="working_hours",
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.RenameField(
            model_name="hospital",
            old_name="validation_status",
            new_name="verification_status",
        ),
    ]
