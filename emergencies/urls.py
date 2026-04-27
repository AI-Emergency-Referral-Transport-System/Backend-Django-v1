from django.urls import path

from emergencies.views import (
    EmergencyListAPIView,
    EmergencyDetailAPIView,
    EmergencySelectHospitalAPIView,
    EmergencyNotesUpdateAPIView,
)

urlpatterns = [
    path("", EmergencyListAPIView.as_view(), name="emergency-list-create"),
    path("<uuid:pk>/", EmergencyDetailAPIView.as_view(), name="emergency-detail"),
    path("<uuid:pk>/select-hospital/", EmergencySelectHospitalAPIView.as_view(), name="emergency-select-hospital"),
    path("<uuid:pk>/notes/", EmergencyNotesUpdateAPIView.as_view(), name="emergency-notes"),
]
