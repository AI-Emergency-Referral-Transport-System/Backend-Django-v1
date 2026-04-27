from django.urls import path

from hospitals.views import (
    HospitalDetailAPIView,
    HospitalListCreateAPIView,
    HospitalNearbyAPIView,
    HospitalResourceAPIView,
)


app_name = "hospitals"

urlpatterns = [
    path("", HospitalListCreateAPIView.as_view(), name="hospital-list-create"),
    path("register/", HospitalListCreateAPIView.as_view(), name="hospital-register"),
    path("nearby/", HospitalNearbyAPIView.as_view(), name="hospital-nearby"),
    path("<uuid:pk>/", HospitalDetailAPIView.as_view(), name="hospital-detail"),
    path("<uuid:hospital_id>/resources/", HospitalResourceAPIView.as_view(), name="hospital-resources"),
]