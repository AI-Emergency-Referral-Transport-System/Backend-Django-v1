from django.conf import settings
from django.contrib import admin
from django.urls import include, path


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/auth/", include("accounts.urls")),
    path("api/v1/system-admin/", include("system_admin.urls")),
]

if settings.GIS_ENABLED:
    urlpatterns += [
        path("api/v1/tracking/", include("tracking.urls")),
        path("api/v1/emergencies/", include("emergencies.urls")),
        path("api/v1/hospitals/", include("hospitals.urls")),
        path("api/v1/ambulances/", include("ambulances.urls")),
        path("api/v1/ai/", include("ai.urls")),
    ]
