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
from emergencies.models import Emergency
from hospitals.models import Hospital


class AdminDashboardAPIView(APIView):
    permission_classes = [RolePermission]
    allowed_roles = {"admin"}

    def get(self, request):
        data = {
            "total_patients": User.objects.filter(role=User.Role.PATIENT).count(),
            "total_drivers": User.objects.filter(role=User.Role.DRIVER).count(),
            "total_hospitals": Hospital.objects.count(),
            "total_emergencies": Emergency.objects.count(),
            "pending_hospitals": HospitalProfile.objects.filter(
                registration_status=HospitalProfile.RegistrationStatus.PENDING
            ).count(),
            "pending_drivers": DriverProfile.objects.filter(
                verification_status=DriverProfile.VerificationStatus.PENDING
            ).count(),
            "active_emergencies": Emergency.objects.exclude(
                status=Emergency.Status.DELIVERED
            ).count(),
            "completed_emergencies": Emergency.objects.filter(
                status=Emergency.Status.DELIVERED
            ).count(),
        }
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

        Hospital.objects.get_or_create(
            admin=user,
            defaults={
                "name": hospital_profile.hospital_name or "Unnamed Hospital",
                "phone": user.phone_number,
                "available_beds": hospital_profile.available_beds,
            },
        )

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
        hospitals = Hospital.objects.select_related("admin").order_by("-created_at")
        from hospitals.serializers import HospitalSerializer

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
        emergencies = Emergency.objects.select_related(
            "patient", "assigned_ambulance", "selected_hospital"
        ).order_by("-created_at")
        from emergencies.serializers import EmergencySerializer

        serializer = EmergencySerializer(emergencies, many=True)
        return Response(serializer.data)