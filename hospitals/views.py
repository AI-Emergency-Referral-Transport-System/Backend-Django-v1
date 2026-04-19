from django.contrib.gis.geos import Point
from django.contrib.gis.db.models.functions import Distance
from django.shortcuts import get_object_or_404

from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.gis.measure import D 

from common.permissions import RolePermission
from emergencies.models import Emergency
from hospitals.models import Hospital
from hospitals.serializers import HospitalSerializer, HospitalResourceUpdateSerializer


class HospitalListCreateAPIView(generics.ListCreateAPIView):
    """
    GET  /api/hospitals/       — List all hospitals (drivers, hospital_admins)
    POST /api/hospitals/       — Register a new hospital (hospital_admin)
    """
    queryset = Hospital.objects.select_related("admin")
    serializer_class = HospitalSerializer
    permission_classes = [RolePermission]
    allowed_roles = {"driver", "hospital_admin"}


class HospitalDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/hospitals/{id}/  — Retrieve hospital details
    PUT    /api/hospitals/{id}/  — Full update (hospital_admin)
    PATCH  /api/hospitals/{id}/  — Partial update (hospital_admin)
    DELETE /api/hospitals/{id}/  — Delete (hospital_admin)
    """
    queryset = Hospital.objects.select_related("admin")
    serializer_class = HospitalSerializer
    permission_classes = [RolePermission]
    allowed_roles = {"hospital_admin"}


class HospitalResourceUpdateAPIView(APIView):
    """
    PUT /api/hospital/resources/
    Hospital admin updates their own hospital's live resource status
    (beds, ICU, oxygen, specialties, availability).
    """
    permission_classes = [RolePermission]
    allowed_roles = {"hospital_admin"}

    def put(self, request):
        hospital = get_object_or_404(Hospital, admin=request.user)
        serializer = HospitalResourceUpdateSerializer(hospital, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        hospital.refresh_from_db()

        if hospital.available_beds <= 0 and hospital.available_icu_beds <= 0:
            if hospital.is_available:
                hospital.is_available = False
                hospital.save(update_fields=["is_available"])
        else:
            if not hospital.is_available:
                hospital.is_available = True
                hospital.save(update_fields=["is_available"])

        return Response(serializer.data, status=status.HTTP_200_OK)

class HospitalIncomingEmergenciesAPIView(APIView):
    """
    GET /api/hospital/incoming/
    Returns emergencies currently routed to this hospital admin's hospital
    that are in REQUESTED or ASSIGNED state.
    """
    permission_classes = [RolePermission]
    allowed_roles = {"hospital_admin"}

    def get(self, request):
        from emergencies.serializers import EmergencyDetailSerializer
        hospital = get_object_or_404(Hospital, admin=request.user)
        incoming = Emergency.objects.filter(
            hospital=hospital,
            status__in=[Emergency.Status.REQUESTED, Emergency.Status.ASSIGNED],
        ).select_related("patient", "ambulance", "hospital")
        serializer = EmergencyDetailSerializer(incoming, many=True)
        return Response(serializer.data)


class HospitalApproveEmergencyAPIView(APIView):
    """
    POST /api/hospital/approve/{emergency_id}/
    Hospital admin confirms they will accept and prepare for this emergency.
    Status transitions: REQUESTED → ASSIGNED
    """
    permission_classes = [RolePermission]
    allowed_roles = {"hospital_admin"}

    def post(self, request, emergency_id):
        hospital = get_object_or_404(Hospital, admin=request.user)
        emergency = get_object_or_404(Emergency, id=emergency_id, hospital=hospital)

        if emergency.status != Emergency.Status.REQUESTED:
            return Response(
                {"detail": "Only emergencies in 'requested' state can be approved."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        emergency.status = Emergency.Status.ASSIGNED
        emergency.save(update_fields=["status"])
        return Response({"detail": "Emergency approved. Hospital is preparing."}, status=status.HTTP_200_OK)


class HospitalRejectEmergencyAPIView(APIView):
    """
    POST /api/hospital/reject/{emergency_id}/
    Hospital admin rejects the case. Clears the hospital assignment so the
    emergency can be reassigned to another hospital immediately.
    """
    permission_classes = [RolePermission]
    allowed_roles = {"hospital_admin"}

    def post(self, request, emergency_id):
        hospital = get_object_or_404(Hospital, admin=request.user)
        emergency = get_object_or_404(
            Emergency,
            id=emergency_id,
            hospital=hospital,
            status__in=[Emergency.Status.REQUESTED, Emergency.Status.ASSIGNED],
        )

        # Clear hospital so assigment logic can reroute
        emergency.hospital = None
        emergency.status = Emergency.Status.REQUESTED
        emergency.save(update_fields=["hospital", "status"])
        return Response({"detail": "Emergency rejected. It will be reassigned."}, status=status.HTTP_200_OK)


class HospitalPatientArrivedAPIView(APIView):
    """
    POST /api/hospital/arrived/{emergency_id}/
    Hospital admin confirms patient has arrived. Marks emergency as COMPLETED.
    """
    permission_classes = [RolePermission]
    allowed_roles = {"hospital_admin"}

    def post(self, request, emergency_id):
        hospital = get_object_or_404(Hospital, admin=request.user)
        emergency = get_object_or_404(
            Emergency,
            id=emergency_id,
            hospital=hospital,
            status=Emergency.Status.IN_PROGRESS,
        )
        emergency.mark_completed()
        return Response({"detail": "Patient arrival confirmed. Emergency completed."}, status=status.HTTP_200_OK)


class HospitalNearbyAPIView(APIView):
    """
    GET /api/hospitals/nearby/?lat=<lat>&lng=<lng>&radius=<km>
    Returns available hospitals sorted by proximity to the given coordinates.
    Accessible by patients to select a hospital for their emergency.
    """
    permission_classes = [RolePermission]
    allowed_roles = {"patient", "driver", "hospital_admin"}
    
    def get(self, request):
        try:
            lat = float(request.query_params["lat"])
            lng = float(request.query_params["lng"])
        except (KeyError, ValueError):
            return Response(
                {"detail": "Query params 'lat' and 'lng' are required and must be valid numbers."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        radius_km = float(request.query_params.get('radius', 20))
        user_location = Point(lng, lat, srid=4326)

        hospitals = Hospital.objects.filter(
                is_available=True,
                location__distance_lte=(user_location, D(km=radius_km))
            ).annotate(distance=Distance("location", user_location))
        
        if request.query_params.get("need_oxygen") == "true":
            hospitals = hospitals.exclude(oxygen_level=Hospital.OxygenLevel.CRITICAL)
        
        hospitals = hospitals.order_by("distance")

        if not hospitals.exists():
            return Response({
                "message": f"No hospitals with required resources found within {radius_km}km.",
                "hospitals": []
            }, status=status.HTTP_200_OK)
        
        serializer = HospitalSerializer(hospitals, many=True)
        return Response(serializer.data)