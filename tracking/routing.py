from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # 1. Ambulance Tracking: /ws/track/{emergency_id}/
    # This is for patients to watch the ambulance and for drivers to send GPS
    re_path(r'ws/track/(?P<emergency_id>[^/]+)/$', consumers.AmbulanceTrackingConsumer.as_asgi()),

    # 2. Hospital Alerts: /ws/hospital/alerts/{hospital_id}/
    # This is for the hospital dashboard to receive new emergency notifications
    re_path(r'ws/hospital/alerts/(?P<hospital_id>[^/]+)/$', consumers.HospitalNotificationConsumer.as_asgi()),
]