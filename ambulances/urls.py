from django.urls import path
from .views import (
    AmbulanceCreateAPIView,
    AmbulanceListAPIView,
    AmbulanceListCreateAPIView,
    AmbulanceStatusUpdateAPIView,
    DriverAcceptEmergencyAPIView,
    DriverDashboardAPIView,
    DriverDetailAPIView,
    DriverEmergencyActionAPIView,
    DriverGoOnlineAPIView,
    DriverListAPIView,
    DriverLocationAPIView,
    DriverPendingRequestsAPIView,
)


app_name = "ambulances"

urlpatterns = [
    # Hospital Admin - Driver Management
    path("hospital/driver/create/", DriverCreateAPIView.as_view(), name="driver-create"),
    path("hospital/drivers/", DriverListAPIView.as_view(), name="driver-list"),
    path("hospital/driver/<uuid:driver_id>/", DriverDetailAPIView.as_view(), name="driver-detail"),
    
    # Hospital Admin - Ambulance Management
    path("hospital/ambulance/create/", AmbulanceCreateAPIView.as_view(), name="ambulance-create"),
    path("hospital/ambulances/", AmbulanceListAPIView.as_view(), name="ambulance-list"),
    
    # Driver App Endpoints
    path("driver/dashboard/", DriverDashboardAPIView.as_view(), name="driver-dashboard"),
    path("driver/go-online/", DriverGoOnlineAPIView.as_view(), name="driver-go-online"),
    path("driver/location/", DriverLocationAPIView.as_view(), name="driver-location"),
    path("driver/requests/", DriverPendingRequestsAPIView.as_view(), name="driver-requests"),
    path("driver/accept/<uuid:emergency_id>/", DriverAcceptEmergencyAPIView.as_view(), name="driver-accept"),
    path("driver/action/<uuid:emergency_id>/", DriverEmergencyActionAPIView.as_view(), name="driver-action"),
    
    # Base endpoints
    path("", AmbulanceListCreateAPIView.as_view(), name="ambulance-list-create"),
    path("<uuid:pk>/status/", AmbulanceStatusUpdateAPIView.as_view(), name="ambulance-status-update"),
]