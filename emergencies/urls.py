from django.urls import path

from emergencies.views import (
    EmergencyListCreateAPIView,
    EmergencyDetailAPIView,
    EmergencySelectHospitalAPIView,
    EmergencyCancelAPIView,
    EmergencyNotesUpdateAPIView,
)

urlpatterns = [
    path("", EmergencyListCreateAPIView.as_view(), name="emergency-list-create"),
    path("<uuid:pk>/", EmergencyDetailAPIView.as_view(), name="emergency-detail"),
    path("<uuid:pk>/select-hospital/", EmergencySelectHospitalAPIView.as_view(), name="emergency-select-hospital"),
    path("<uuid:pk>/cancel/", EmergencyCancelAPIView.as_view(), name="emergency-cancel"),
    path("<uuid:pk>/notes/", EmergencyNotesUpdateAPIView.as_view(), name="emergency-notes"),
]
