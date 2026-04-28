from django.conf import settings
from django.contrib import admin
from django.urls import include, path


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/admin/", include(("system_admin.urls", "system_admin"), namespace="api-auth-admin")),
    path("api/auth/", include(("accounts.urls", "accounts"), namespace="api-auth")),
    path("api/system-admin/", include(("system_admin.urls", "system_admin"), namespace="api-system-admin")),
    path("api/v1/auth/", include(("accounts.urls", "accounts"), namespace="api-v1-auth")),
    path("api/v1/system-admin/", include(("system_admin.urls", "system_admin"), namespace="api-v1-system-admin")),
]

if settings.GIS_ENABLED:
    urlpatterns += [
        path("api/tracking/", include(("tracking.urls", "tracking"), namespace="api-tracking")),
        path("api/emergencies/", include(("emergencies.urls", "emergencies"), namespace="api-emergencies")),
        path("api/hospitals/", include(("hospitals.urls", "hospitals"), namespace="api-hospitals")),
        path("api/ambulances/", include(("ambulances.urls", "ambulances"), namespace="api-ambulances")),
        path("api/v1/tracking/", include(("tracking.urls", "tracking"), namespace="api-v1-tracking")),
        path("api/v1/emergencies/", include(("emergencies.urls", "emergencies"), namespace="api-v1-emergencies")),
        path("api/v1/hospitals/", include(("hospitals.urls", "hospitals"), namespace="api-v1-hospitals")),
        path("api/v1/ambulances/", include(("ambulances.urls", "ambulances"), namespace="api-v1-ambulances")),
    ]
