from django.urls import path

from system_admin.views import (
    AdminAllDriversAPIView,
    AdminAllEmergenciesAPIView,
    AdminAllHospitalsAPIView,
    AdminApproveDriverAPIView,
    AdminApproveHospitalAPIView,
    AdminDashboardAPIView,
    AdminPendingDriversAPIView,
    AdminPendingHospitalsAPIView,
    AdminRejectDriverAPIView,
    AdminRejectHospitalAPIView,
)

urlpatterns = [
    path("dashboard/", AdminDashboardAPIView.as_view(), name="admin-dashboard"),
    path("hospitals/pending/", AdminPendingHospitalsAPIView.as_view(), name="admin-pending-hospitals"),
    path("hospitals/approve/<uuid:hospital_profile_id>/", AdminApproveHospitalAPIView.as_view(), name="admin-approve-hospital"),
    path("hospitals/reject/<uuid:hospital_profile_id>/", AdminRejectHospitalAPIView.as_view(), name="admin-reject-hospital"),
    path("hospitals/", AdminAllHospitalsAPIView.as_view(), name="admin-all-hospitals"),
    path("drivers/pending/", AdminPendingDriversAPIView.as_view(), name="admin-pending-drivers"),
    path("drivers/approve/<uuid:driver_profile_id>/", AdminApproveDriverAPIView.as_view(), name="admin-approve-driver"),
    path("drivers/reject/<uuid:driver_profile_id>/", AdminRejectDriverAPIView.as_view(), name="admin-reject-driver"),
    path("drivers/", AdminAllDriversAPIView.as_view(), name="admin-all-drivers"),
    path("emergencies/", AdminAllEmergenciesAPIView.as_view(), name="admin-all-emergencies"),
]