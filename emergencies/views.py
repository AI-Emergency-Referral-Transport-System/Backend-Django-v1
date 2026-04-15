from django.shortcuts import get_object_or_404

from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from common.permissions import RolePermission
from emergencies.models import Emergency
from emergencies.serializers import (
    EmergencySerializer,
    EmergencyDetailSerializer,
    EmergencySelectHospitalSerializer,
    EmergencyNotesUpdateSerializer,
)
from hospitals.models import Hospital


class EmergencyListCreateAPIView(generics.ListCreateAPIView):
    """
    GET  /api/emergency/  — List emergencies (filtered by patient or role)
    POST /api/emergency/  — Create a new emergency request (patient only)
    """
    serializer_class = EmergencySerializer
    permission_classes = [RolePermission]
    allowed_roles = {"patient", "driver", "hospital_admin"}

    def get_queryset(self):
        user = self.request.user
        qs = Emergency.objects.select_related("patient", "ambulance", "hospital")
        # Patients only see their own emergencies
        if getattr(user, "role", None) == "patient":
            return qs.filter(patient=user)
        return qs

    def perform_create(self, serializer):
        serializer.save(patient=self.request.user, status=Emergency.Status.REQUESTED)


class EmergencyDetailAPIView(generics.RetrieveAPIView):
    """
    GET /api/emergency/{id}/  — Retrieve full emergency details
    Patients can only view their own. Drivers and hospital admins can view any.
    """
    serializer_class = EmergencyDetailSerializer
    permission_classes = [RolePermission]
    allowed_roles = {"patient", "driver", "hospital_admin"}

    def get_object(self):
        user = self.request.user
        qs = Emergency.objects.select_related("patient", "ambulance", "hospital")
        if getattr(user, "role", None) == "patient":
            qs = qs.filter(patient=user)
        return get_object_or_404(qs, id=self.kwargs["pk"])


class EmergencySelectHospitalAPIView(APIView):
    """
    POST /api/emergency/{id}/select-hospital/
    Patient selects their preferred hospital from the list suggested by the AI.
    Immediately reassigns the hospital on the emergency record.
    """
    permission_classes = [RolePermission]
    allowed_roles = {"patient"}

    def post(self, request, pk):
        emergency = get_object_or_404(Emergency, id=pk, patient=request.user)

        if emergency.status not in (Emergency.Status.REQUESTED, Emergency.Status.ASSIGNED):
            return Response(
                {"detail": "Hospital can only be selected while the emergency is in 'requested' or 'assigned' state."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = EmergencySelectHospitalSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        hospital = get_object_or_404(Hospital, id=serializer.validated_data["hospital_id"], is_available=True)

        # Immediately reassign the hospital
        emergency.hospital = hospital
        emergency.status = Emergency.Status.REQUESTED
        emergency.save(update_fields=["hospital", "status"])

        return Response(
            {"detail": f"Hospital '{hospital.name}' selected. Awaiting approval."},
            status=status.HTTP_200_OK,
        )


class EmergencyCancelAPIView(APIView):
    """
    POST /api/emergency/{id}/cancel/
    Patient cancels their emergency request if it hasn't been completed yet.
    """
    permission_classes = [RolePermission]
    allowed_roles = {"patient"}

    def post(self, request, pk):
        emergency = get_object_or_404(Emergency, id=pk, patient=request.user)

        if emergency.status == Emergency.Status.COMPLETED:
            return Response(
                {"detail": "Cannot cancel a completed emergency."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if emergency.status == Emergency.Status.CANCELLED:
            return Response(
                {"detail": "Emergency is already cancelled."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        emergency.status = Emergency.Status.CANCELLED
        emergency.save(update_fields=["status"])
        return Response({"detail": "Emergency cancelled successfully."}, status=status.HTTP_200_OK)


class EmergencyNotesUpdateAPIView(APIView):
    """
    PATCH /api/emergency/{id}/notes/
    Allows drivers and hospital admins to add progress notes to an active emergency.
    """
    permission_classes = [RolePermission]
    allowed_roles = {"driver", "hospital_admin"}

    def patch(self, request, pk):
        emergency = get_object_or_404(
            Emergency,
            id=pk,
            status__in=[Emergency.Status.ASSIGNED, Emergency.Status.IN_PROGRESS],
        )
        serializer = EmergencyNotesUpdateSerializer(emergency, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
