from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # Match the /ws/track/{emergency_id}/ requirement
    re_path(r'ws/track/(?P<emergency_id>[^/]+)/$', consumers.AmbulanceTrackingConsumer.as_async()),
]

