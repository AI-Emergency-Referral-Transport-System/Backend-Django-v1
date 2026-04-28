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
from hospitals.services import HospitalSelectionService


class EmergencyListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = EmergencySerializer
    permission_classes = [RolePermission]
    allowed_roles = {"patient", "driver", "hospital_admin"}
    hospital_selection_service = HospitalSelectionService()

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
        pickup_latitude = data.get("pickup_latitude")
        pickup_longitude = data.get("pickup_longitude")
        if pickup_latitude is None or pickup_longitude is None:
            return Response(
                {
                    "success": False,
                    "errors": {"detail": "pickup_latitude and pickup_longitude are required."},
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        selected_hospital = None
        hospital_id = data.get("hospital_id")
        if hospital_id:
            from hospitals.models import Hospital

            selected_hospital = get_object_or_404(Hospital, id=hospital_id, is_available=True)

        emergency = Emergency.objects.create(
            patient=request.user,
            emergency_type=data.get("emergency_type", "medical"),
            priority=data.get("priority", "medium"),
            status=Emergency.Status.PENDING,
            patient_description=data.get("description", ""),
            description=data.get("description", ""),
            selected_hospital=selected_hospital,
            patient_location=Point(float(pickup_longitude), float(pickup_latitude), srid=4326),
            pickup_address=data.get("pickup_address", ""),
            patient_name=data.get("patient_name", ""),
            patient_age=data.get("patient_age"),
            patient_condition=data.get("patient_condition", ""),
            patient_phone=data.get("patient_phone", ""),
            summary=data.get("summary", ""),
            notes=data.get("notes", ""),
        )
        suggestions = self.hospital_selection_service.sync_emergency_suggestions(emergency)
        if selected_hospital is not None:
            selected_suggestion = self.hospital_selection_service.mark_selected_hospital(emergency, selected_hospital)
            emergency.selected_hospital = selected_hospital
            emergency.distance_km = selected_suggestion.distance_km
            emergency.save()
        recommended_hospital = emergency.selected_hospital

        return Response(
            {
                "success": True,
                "message": "Emergency created successfully",
                "emergency_id": str(emergency.id),
                "recommended_hospital": (
                    {
                        "id": str(recommended_hospital.id),
                        "name": recommended_hospital.name,
                    }
                    if recommended_hospital
                    else None
                ),
                "hospital_suggestions": [
                    {
                        "hospital_id": str(suggestion.hospital_id),
                        "hospital_name": suggestion.hospital.name,
                        "distance_km": suggestion.distance_km,
                        "score": suggestion.score,
                        "reason": suggestion.reason,
                        "is_selected": suggestion.is_selected,
                    }
                    for suggestion in suggestions
                ],
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
    hospital_selection_service = HospitalSelectionService()

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

        suggestion = self.hospital_selection_service.mark_selected_hospital(emergency, hospital)
        emergency.selected_hospital = hospital
        emergency.distance_km = suggestion.distance_km
        emergency.save()

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
