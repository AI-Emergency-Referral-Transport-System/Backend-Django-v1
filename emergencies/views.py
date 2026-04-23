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


class EmergencyListAPIView(generics.ListCreateAPIView):
    """
    GET  /api/emergency/  — List emergencies (filtered by patient or role)
    """
    serializer_class = EmergencySerializer
    permission_classes = [RolePermission]
    allowed_roles = {"patient", "driver", "hospital_admin"}

    def get_queryset(self):
        user = self.request.user
        qs = Emergency.objects.select_related("patient", "assigned_ambulance", "selected_hospital")
        if getattr(user, "role", None) == "patient":
            return qs.filter(patient=user)
        return qs


class EmergencyListCreateAPIView(EmergencyListAPIView):
    pass

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
        qs = Emergency.objects.select_related("patient", "assigned_ambulance", "selected_hospital")
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

        if emergency.status not in (Emergency.Status.PENDING, Emergency.Status.ACCEPTED):
            return Response(
                {"detail": "Hospital can only be selected while the emergency is pending or accepted."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = EmergencySelectHospitalSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        hospital = get_object_or_404(Hospital, id=serializer.validated_data["hospital_id"], is_available=True)

        emergency.selected_hospital = hospital
        emergency.save(update_fields=["selected_hospital"])

        return Response(
            {"detail": f"Hospital '{hospital.name}' selected. Awaiting approval."},
            status=status.HTTP_200_OK,
        )


class EmergencyCancelAPIView(APIView):
    permission_classes = [RolePermission]
    allowed_roles = {"patient"}

    def post(self, request, pk):
        emergency = get_object_or_404(Emergency, id=pk, patient=request.user)
        emergency.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class EmergencyNotesUpdateAPIView(APIView):
    """
    PATCH /api/emergency/{id}/notes/
    Allows drivers and hospital admins to add progress notes to an active emergency.
    """
    permission_classes = [RolePermission]
    allowed_roles = {"driver", "hospital_admin"}

    def patch(self, request, pk):
        emergency = get_object_or_404(Emergency, id=pk)
        serializer = EmergencyNotesUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        emergency.patient_description = serializer.validated_data["patient_description"]
        emergency.save(update_fields=["patient_description"])
        return Response({"patient_description": emergency.patient_description}, status=status.HTTP_200_OK)
