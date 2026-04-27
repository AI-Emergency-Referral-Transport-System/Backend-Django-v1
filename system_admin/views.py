from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import DriverProfile, HospitalProfile, User
from system_admin.serializers import (
    AdminDashboardSerializer,
    AdminDriverProfileSerializer,
    AdminHospitalProfileSerializer,
)
from common.permissions import RolePermission


class AdminDashboardAPIView(APIView):
    permission_classes = [RolePermission]
    allowed_roles = {"admin"}

    def get(self, request):
        from django.conf import settings
        
        data = {
            "total_patients": User.objects.filter(role=User.Role.PATIENT).count(),
            "total_drivers": User.objects.filter(role=User.Role.DRIVER).count(),
            "total_hospital_admins": User.objects.filter(role=User.Role.HOSPITAL_ADMIN).count(),
            "pending_hospitals": HospitalProfile.objects.filter(
                registration_status=HospitalProfile.RegistrationStatus.PENDING
            ).count(),
            "pending_drivers": DriverProfile.objects.filter(
                verification_status=DriverProfile.VerificationStatus.PENDING
            ).count(),
        }
        
        if settings.GIS_ENABLED:
            try:
                from emergencies.models import Emergency
                data["total_emergencies"] = Emergency.objects.count()
                data["active_emergencies"] = Emergency.objects.exclude(
                    status=Emergency.Status.DELIVERED
                ).count()
                data["completed_emergencies"] = Emergency.objects.filter(
                    status=Emergency.Status.DELIVERED
                ).count()
            except Exception:
                data["total_emergencies"] = 0
                data["active_emergencies"] = 0
                data["completed_emergencies"] = 0
        else:
            data["total_emergencies"] = 0
            data["active_emergencies"] = 0
            data["completed_emergencies"] = 0
            data["gis_enabled"] = False
            
        serializer = AdminDashboardSerializer(data)
        return Response(serializer.data)


class AdminPendingHospitalsAPIView(APIView):
    permission_classes = [RolePermission]
    allowed_roles = {"admin"}

    def get(self, request):
        pending = HospitalProfile.objects.filter(
            registration_status=HospitalProfile.RegistrationStatus.PENDING
        ).select_related("user")
        serializer = AdminHospitalProfileSerializer(pending, many=True)
        return Response(serializer.data)


class AdminApproveHospitalAPIView(APIView):
    permission_classes = [RolePermission]
    allowed_roles = {"admin"}

    def post(self, request, hospital_profile_id):
        hospital_profile = get_object_or_404(
            HospitalProfile, id=hospital_profile_id
        )

        if hospital_profile.registration_status != HospitalProfile.RegistrationStatus.PENDING:
            return Response(
                {"detail": "Hospital already processed."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        hospital_profile.registration_status = HospitalProfile.RegistrationStatus.APPROVED
        hospital_profile.save(update_fields=["registration_status"])

        user = hospital_profile.user
        user.is_verified = True
        user.save(update_fields=["is_verified"])

        return Response(
            {"detail": "Hospital approved successfully."},
            status=status.HTTP_200_OK,
        )


class AdminRejectHospitalAPIView(APIView):
    permission_classes = [RolePermission]
    allowed_roles = {"admin"}

    def post(self, request, hospital_profile_id):
        hospital_profile = get_object_or_404(
            HospitalProfile, id=hospital_profile_id
        )

        if hospital_profile.registration_status != HospitalProfile.RegistrationStatus.PENDING:
            return Response(
                {"detail": "Hospital already processed."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        hospital_profile.registration_status = HospitalProfile.RegistrationStatus.REJECTED
        hospital_profile.save(update_fields=["registration_status"])

        return Response(
            {"detail": "Hospital rejected."},
            status=status.HTTP_200_OK,
        )


class AdminPendingDriversAPIView(APIView):
    permission_classes = [RolePermission]
    allowed_roles = {"admin"}

    def get(self, request):
        pending = DriverProfile.objects.filter(
            verification_status=DriverProfile.VerificationStatus.PENDING
        ).select_related("user")
        serializer = AdminDriverProfileSerializer(pending, many=True)
        return Response(serializer.data)


class AdminApproveDriverAPIView(APIView):
    permission_classes = [RolePermission]
    allowed_roles = {"admin"}

    def post(self, request, driver_profile_id):
        driver_profile = get_object_or_404(DriverProfile, id=driver_profile_id)

        if driver_profile.verification_status != DriverProfile.VerificationStatus.PENDING:
            return Response(
                {"detail": "Driver already processed."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        driver_profile.verification_status = DriverProfile.VerificationStatus.APPROVED
        driver_profile.save(update_fields=["verification_status"])

        user = driver_profile.user
        user.is_verified = True
        user.save(update_fields=["is_verified"])

        return Response(
            {"detail": "Driver approved successfully."},
            status=status.HTTP_200_OK,
        )


class AdminRejectDriverAPIView(APIView):
    permission_classes = [RolePermission]
    allowed_roles = {"admin"}

    def post(self, request, driver_profile_id):
        driver_profile = get_object_or_404(DriverProfile, id=driver_profile_id)

        if driver_profile.verification_status != DriverProfile.VerificationStatus.PENDING:
            return Response(
                {"detail": "Driver already processed."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        driver_profile.verification_status = DriverProfile.VerificationStatus.REJECTED
        driver_profile.save(update_fields=["verification_status"])

        return Response(
            {"detail": "Driver rejected."},
            status=status.HTTP_200_OK,
        )


class AdminAllHospitalsAPIView(APIView):
    permission_classes = [RolePermission]
    allowed_roles = {"admin"}

    def get(self, request):
        from django.conf import settings
        if not settings.GIS_ENABLED:
            return Response(
                {"detail": "Hospitals not available - GDAL required."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        from hospitals.models import Hospital
        from hospitals.serializers import HospitalSerializer

        hospitals = Hospital.objects.select_related("admin").order_by("-created_at")
        serializer = HospitalSerializer(hospitals, many=True)
        return Response(serializer.data)


class AdminAllDriversAPIView(APIView):
    permission_classes = [RolePermission]
    allowed_roles = {"admin"}

    def get(self, request):
        drivers = DriverProfile.objects.select_related("user").order_by("-created_at")
        serializer = AdminDriverProfileSerializer(drivers, many=True)
        return Response(serializer.data)


class AdminAllEmergenciesAPIView(APIView):
    permission_classes = [RolePermission]
    allowed_roles = {"admin"}

    def get(self, request):
        from django.conf import settings
        if not settings.GIS_ENABLED:
            return Response(
                {"detail": "Emergencies not available - GDAL required."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        from emergencies.models import Emergency
        from emergencies.serializers import EmergencySerializer

        emergencies = Emergency.objects.select_related(
            "patient", "assigned_ambulance", "selected_hospital"
        ).order_by("-created_at")
        serializer = EmergencySerializer(emergencies, many=True)
        return Response(serializer.data)