from django.conf import settings
from django.contrib.gis.geos import Point
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


class EmergencyListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = EmergencySerializer
    permission_classes = [RolePermission]
    allowed_roles = {"patient", "driver", "hospital_admin"}

    def get_queryset(self):
        if not settings.GIS_ENABLED:
            return Emergency.objects.none()
        
        user = self.request.user
        qs = Emergency.objects.select_related("patient", "assigned_ambulance", "selected_hospital")
        if getattr(user, "role", None) == "patient":
            return qs.filter(patient=user)
        return qs

    def create(self, request):
        if not settings.GIS_ENABLED:
            return Response(
                {"success": False, "errors": {"detail": "GIS required."}},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        data = request.data
        emergency = Emergency.objects.create(
            patient=request.user,
            emergency_type=data.get("emergency_type", "medical"),
            priority=data.get("priority", "medium"),
            patient_description=data.get("description", ""),
            patient_location=Point(data.get("pickup_longitude"), data.get("pickup_latitude"), srid=4326)
            if data.get("pickup_latitude") and data.get("pickup_longitude")
            else None,
        )

        return Response(
            {
                "success": True,
                "message": "Emergency created successfully",
                "emergency_id": str(emergency.id),
            },
            status=status.HTTP_201_CREATED,
        )


class EmergencyDetailAPIView(generics.RetrieveAPIView):
    serializer_class = EmergencyDetailSerializer
    permission_classes = [RolePermission]
    allowed_roles = {"patient", "driver", "hospital_admin"}

    def get_object(self):
        if not settings.GIS_ENABLED:
            return Emergency.objects.none()
        
        user = self.request.user
        qs = Emergency.objects.select_related("patient", "assigned_ambulance", "selected_hospital")
        if getattr(user, "role", None) == "patient":
            qs = qs.filter(patient=user)
        return get_object_or_404(qs, id=self.kwargs["pk"])


class EmergencyMyListAPIView(APIView):
    permission_classes = [RolePermission]
    allowed_roles = {"patient"}

    def get(self, request):
        if not settings.GIS_ENABLED:
            return Response(
                {"success": True, "emergencies": [], "count": 0},
                status=status.HTTP_200_OK,
            )

        emergencies = Emergency.objects.filter(patient=request.user).order_by("-created_at")
        results = []
        for e in emergencies:
            results.append(
                {
                    "id": str(e.id),
                    "emergency_type": e.emergency_type,
                    "priority": e.priority,
                    "status": e.status,
                    "created_at": e.created_at.isoformat(),
                }
            )

        return Response(
            {"success": True, "emergencies": results, "count": len(results)},
            status=status.HTTP_200_OK,
        )


class EmergencySelectHospitalAPIView(APIView):
    permission_classes = [RolePermission]
    allowed_roles = {"patient"}

    def post(self, request, pk):
        if not settings.GIS_ENABLED:
            return Response(
                {"success": False, "errors": {"detail": "GIS required."}},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        emergency = get_object_or_404(Emergency, id=pk, patient=request.user)

        if emergency.status not in [Emergency.Status.PENDING, Emergency.Status.ACCEPTED]:
            return Response(
                {"success": False, "errors": {"detail": "Hospital can only be selected while pending/accepted."}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = EmergencySelectHospitalSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        from hospitals.models import Hospital

        hospital = get_object_or_404(
            Hospital, id=serializer.validated_data["hospital_id"], is_available=True
        )

        emergency.selected_hospital = hospital
        emergency.save(update_fields=["selected_hospital"])

        return Response(
            {"success": True, "message": f"Hospital '{hospital.name}' selected."},
            status=status.HTTP_200_OK,
        )


class EmergencyCancelAPIView(APIView):
    permission_classes = [RolePermission]
    allowed_roles = {"patient"}

    def post(self, request, pk):
        emergency = get_object_or_404(Emergency, id=pk, patient=request.user)
        emergency.delete()
        return Response(
            {"success": True, "message": "Emergency cancelled"},
            status=status.HTTP_200_OK,
        )


class EmergencyNotesUpdateAPIView(APIView):
    permission_classes = [RolePermission]
    allowed_roles = {"driver", "hospital_admin"}

    def patch(self, request, pk):
        if not settings.GIS_ENABLED:
            return Response(
                {"success": False, "errors": {"detail": "GIS required."}},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        emergency = get_object_or_404(Emergency, id=pk)
        serializer = EmergencyNotesUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        emergency.patient_description = serializer.validated_data.get("patient_description", "")
        emergency.save(update_fields=["patient_description"])
        return Response(
            {"success": True, "message": "Notes updated"},
            status=status.HTTP_200_OK,
        )