from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import User
from accounts.permissions import RolePermission
from ambulances.models import Ambulance
from emergencies.models import Emergency
from hospitals.models import Hospital
from tracking.models import Location_Track
from tracking.serializers import EmergencySerializer


class CreateEmergencyAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated, RolePermission]
    allowed_roles = {User.Role.PATIENT}

    @transaction.atomic
    def post(self, request):
        lat = request.data.get("lat", request.data.get("pickup_latitude"))
        lon = request.data.get("lon", request.data.get("pickup_longitude"))
        hospital_id = request.data.get("hospital_id")

        if lat is None or lon is None:
            return Response({"error": "Coordinates required"}, status=status.HTTP_400_BAD_REQUEST)

        patient_coords = Point(float(lon), float(lat), srid=4326)
        hospital = None
        if hospital_id:
            hospital = get_object_or_404(Hospital, id=hospital_id)

        emergency = Emergency.objects.create(
            patient=request.user,
            patient_location=patient_coords,
            selected_hospital=hospital,
            status=Emergency.Status.PENDING,
            emergency_type=request.data.get("emergency_type", "medical"),
            priority=request.data.get("priority", Emergency.Priority.MEDIUM),
            patient_description=request.data.get("description", ""),
            description=request.data.get("description", ""),
            pickup_address=request.data.get("pickup_address", ""),
        )

        serializer = EmergencySerializer(emergency)

        nearby_ambulances = Ambulance.objects.filter(
            status=Ambulance.Status.AVAILABLE,
            current_location__distance_lte=(patient_coords, D(km=20)),
        )

        channel_layer = get_channel_layer()
        for ambulance in nearby_ambulances:
            async_to_sync(channel_layer.group_send)(
                f"ambulance_driver_{ambulance.id}",
                {
                    "type": "new_emergency_alert",
                    "data": {
                        "emergency_id": str(emergency.id),
                        "patient_lat": float(lat),
                        "patient_lon": float(lon),
                        "emergency_data": serializer.data,
                    },
                },
            )

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class AcceptEmergencyAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated, RolePermission]
    allowed_roles = {User.Role.DRIVER}

    @transaction.atomic
    def post(self, request, ambulance_id, emergency_id):
        emergency = Emergency.objects.select_for_update().get(id=emergency_id)

        if emergency.assigned_ambulance is not None:
            return Response({"error": "Already accepted by another driver."}, status=status.HTTP_400_BAD_REQUEST)

        ambulance = get_object_or_404(Ambulance, id=ambulance_id, driver=request.user)

        emergency.assigned_ambulance = ambulance
        emergency.status = Emergency.Status.ACCEPTED
        emergency.save(update_fields=["assigned_ambulance", "status"])

        ambulance.status = Ambulance.Status.EN_ROUTE
        ambulance.save(update_fields=["status"])

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"emergency_{emergency_id}",
            {
                "type": "assignment_notification",
                "ambulance_id": str(ambulance.id),
                "plate_number": ambulance.plate_number,
                "status": "Ambulance En Route",
            },
        )

        return Response(
            {
                "status": "success",
                "patient_lat": emergency.patient_location.y if emergency.patient_location else None,
                "patient_lon": emergency.patient_location.x if emergency.patient_location else None,
            }
        )


class PickupPatientAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated, RolePermission]
    allowed_roles = {User.Role.DRIVER}

    def post(self, request, emergency_id):
        emergency = get_object_or_404(Emergency, id=emergency_id)

        if emergency.assigned_ambulance is None or emergency.assigned_ambulance.driver != request.user:
            return Response(
                {"error": "You are not authorized to update this mission."},
                status=status.HTTP_403_FORBIDDEN,
            )

        emergency.status = Emergency.Status.RETRIEVED
        emergency.save(update_fields=["status"])

        hospital = emergency.selected_hospital
        return Response(
            {
                "status": "success",
                "hospital_name": hospital.name if hospital else None,
                "hospital_lat": hospital.location.y if hospital and hospital.location else None,
                "hospital_lon": hospital.location.x if hospital and hospital.location else None,
            },
            status=status.HTTP_200_OK,
        )


class CompleteMissionAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated, RolePermission]
    allowed_roles = {User.Role.DRIVER}

    def post(self, request, emergency_id):
        emergency = get_object_or_404(Emergency, id=emergency_id)

        if emergency.assigned_ambulance is None or emergency.assigned_ambulance.driver != request.user:
            return Response(
                {"error": "Unauthorized action."},
                status=status.HTTP_403_FORBIDDEN,
            )

        emergency.mark_completed()

        ambulance = emergency.assigned_ambulance
        ambulance.status = Ambulance.Status.AVAILABLE
        ambulance.save(update_fields=["status"])

        return Response({"status": "mission_completed"}, status=status.HTTP_200_OK)


def assign_hospital_to_emergency(emergency, hospital):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"hospital_{hospital.id}",
        {
            "type": "new_emergency_alert",
            "emergency_id": str(emergency.id),
            "patient_name": emergency.patient.full_name,
        },
    )


class EmergencyTrackingDetailAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, emergency_id):
        emergency = get_object_or_404(
            Emergency.objects.select_related("patient", "assigned_ambulance", "selected_hospital"),
            id=emergency_id,
        )

        latest_location = (
            Location_Track.objects.filter(emergency=emergency)
            .select_related("ambulance")
            .order_by("-timestamp")
            .first()
        )

        data = EmergencySerializer(emergency).data
        data["assigned_ambulance_id"] = (
            str(emergency.assigned_ambulance_id) if emergency.assigned_ambulance_id else None
        )
        data["latest_location"] = (
            {
                "ambulance_id": str(latest_location.ambulance_id),
                "latitude": latest_location.coordinates.y,
                "longitude": latest_location.coordinates.x,
                "speed": latest_location.speed,
                "heading": latest_location.heading,
                "accuracy": latest_location.accuracy,
                "timestamp": latest_location.timestamp.isoformat(),
            }
            if latest_location
            else None
        )
        return Response(data, status=status.HTTP_200_OK)


class AmbulanceLatestLocationAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, ambulance_id):
        ambulance = get_object_or_404(Ambulance, id=ambulance_id)
        latest_location = Location_Track.objects.filter(ambulance=ambulance).order_by("-timestamp").first()

        if latest_location:
            payload = {
                "ambulance_id": str(ambulance.id),
                "plate_number": ambulance.plate_number,
                "status": ambulance.status,
                "latitude": latest_location.coordinates.y,
                "longitude": latest_location.coordinates.x,
                "speed": latest_location.speed,
                "heading": latest_location.heading,
                "accuracy": latest_location.accuracy,
                "timestamp": latest_location.timestamp.isoformat(),
            }
        elif getattr(ambulance, "current_location", None):
            payload = {
                "ambulance_id": str(ambulance.id),
                "plate_number": ambulance.plate_number,
                "status": ambulance.status,
                "latitude": ambulance.current_location.y,
                "longitude": ambulance.current_location.x,
                "speed": None,
                "heading": None,
                "accuracy": None,
                "timestamp": (
                    ambulance.last_location_update.isoformat() if ambulance.last_location_update else None
                ),
            }
        else:
            payload = {
                "ambulance_id": str(ambulance.id),
                "plate_number": ambulance.plate_number,
                "status": ambulance.status,
                "latitude": None,
                "longitude": None,
                "speed": None,
                "heading": None,
                "accuracy": None,
                "timestamp": None,
            }

        return Response(payload, status=status.HTTP_200_OK)
