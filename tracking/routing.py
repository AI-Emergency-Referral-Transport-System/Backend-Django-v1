from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # 1. Ambulance Tracking: /ws/track/{emergency_id}/
    # This is for patients to watch the ambulance and for drivers to send GPS
    re_path(
        r'ws/tracking/(?P<emergency_id>\w+)/$', 
        consumers.AmbulanceTrackingConsumer.as_asgi()
    ),

    # 2. For the Driver (Receiving new mission alerts)
    re_path(
       r'ws/dispatch/(?P<ambulance_id>[0-9a-f-]+)/$',
        consumers.DispatchConsumer.as_asgi()
    ),

    # 3. Hospital Alerts: /ws/hospital/alerts/{hospital_id}/
    # This is for the hospital dashboard to receive new emergency notifications
    re_path(r'ws/hospital/alerts/(?P<hospital_id>[^/]+)/$', consumers.HospitalNotificationConsumer.as_asgi()),
]
