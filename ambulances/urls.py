from django.urls import path
from .views import (
    AmbulanceListCreateAPIView, 
    # DriverAcceptEmergencyAPIView, 
    # AmbulanceStatusUpdateAPIView
)

urlpatterns = [
    # # 1. Base list/create endpoint 
    # path("", AmbulanceListCreateAPIView.as_view(), name="ambulance-list-create"),

    # # 2. Driver Acceptance Endpoint 
    # # This matches the documentation: POST /api/driver/accept/{emergency_id}/
    # path(
    #     "driver/accept/<uuid:emergency_id>/", 
    #     DriverAcceptEmergencyAPIView.as_view(), 
    #     name="driver-accept-emergency"
    # ),

    # # 3. Status & Location Update Endpoint 
    # # This matches the API Reference: PUT /api/ambulances/{id}/status/
    # path(
    #     "<uuid:pk>/status/", 
    #     AmbulanceStatusUpdateAPIView.as_view(), 
    #     name="ambulance-status-update"
    # ),
]