from django.urls import path
from .views import (
    AcceptEmergencyAPIView,
    AmbulanceLatestLocationAPIView,
    CompleteMissionAPIView,
    CreateEmergencyAPIView,
    EmergencyTrackingDetailAPIView,
    PickupPatientAPIView,
)

app_name = 'tracking'
urlpatterns = [
    path('emergency/<uuid:emergency_id>/', EmergencyTrackingDetailAPIView.as_view(), name='tracking-emergency-detail'),
    path('ambulance/<uuid:ambulance_id>/latest/', AmbulanceLatestLocationAPIView.as_view(), name='tracking-ambulance-latest'),
    # path('nearest-hospitals/', views.find_nearest_hospitals, name='nearest_hospitals'),
    path('api/accept-emergency/<uuid:ambulance_id>/<uuid:emergency_id>/', 
         AcceptEmergencyAPIView.as_view(), name='accept_emergency'
    ),
    path('api/create-emergency/', CreateEmergencyAPIView.as_view(), name='create_emergency'),
    path('api/pickup-patient/<uuid:emergency_id>/', PickupPatientAPIView.as_view(), name='pickup_patient'),
    path('api/complete-mission/<uuid:emergency_id>/', CompleteMissionAPIView.as_view(), name='complete_mission'),
]
