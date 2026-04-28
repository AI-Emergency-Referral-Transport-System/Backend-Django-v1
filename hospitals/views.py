from django.conf import settings
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from common.permissions import RolePermission
from hospitals.models import Hospital
from hospitals.serializers import (
    HospitalListSerializer,
    HospitalRegistrationSerializer,
    HospitalResourceSerializer,
    HospitalResourceUpdateSerializer,
    HospitalSerializer,
)


def _require_gis_response():
    return Response(
        {"error": "Hospitals not available - GDAL required."},
        status=status.HTTP_503_SERVICE_UNAVAILABLE,
    )


class HospitalRootAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return Response(
            {
                "message": "Hospitals API is available.",
                "endpoints": {
                    "list": "/api/hospitals/",
                    "register": "/api/hospitals/register/",
                    "nearby": "/api/hospitals/nearby/",
                    "resources": "/api/hospitals/{id}/resources/",
                },
            },
            status=status.HTTP_200_OK,
        )


class HospitalListCreateAPIView(generics.ListCreateAPIView):
    queryset = Hospital.objects.all()
    serializer_class = HospitalListSerializer

    def get_permissions(self):
        if self.request.method in {"GET", "POST"}:
            return [permissions.AllowAny()]
        return [RolePermission()]

    def get_queryset(self):
        if not settings.GIS_ENABLED:
            return Hospital.objects.none()
        return Hospital.objects.all()

    def list(self, request):
        if not settings.GIS_ENABLED:
            return _require_gis_response()

        queryset = self.get_queryset()
        city = request.query_params.get("city")
        specialty = request.query_params.get("specialty")
        has_emergency = request.query_params.get("has_emergency")
        search = request.query_params.get("search")

        if city:
            queryset = queryset.filter(city__icontains=city)
        if specialty == "emergency":
            queryset = queryset.filter(has_emergency=True)
        if has_emergency is not None:
            has_emergency_bool = str(has_emergency).lower() in {"1", "true", "yes", "on"}
            queryset = queryset.filter(has_emergency=has_emergency_bool)
        if search:
            queryset = queryset.filter(name__icontains=search) | queryset.filter(address__icontains=search)

        serializer = HospitalListSerializer(queryset.order_by("name"), many=True)
        return Response(
            {"count": queryset.count(), "results": serializer.data},
            status=status.HTTP_200_OK,
        )

    def create(self, request):
        if not settings.GIS_ENABLED:
            return _require_gis_response()

        from accounts.models import HospitalProfile, User
        from accounts.profiles.services import ensure_profile_bundle

        serializer = HospitalRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        admin_email = data.get("admin_email", data.get("email"))
        if not admin_email:
            return Response(
                {"success": False, "errors": {"admin_email": ["Required."]}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if User.objects.filter(email=admin_email).exists():
            return Response(
                {"success": False, "errors": {"admin_email": ["Email already registered."]}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if data.get("latitude") is None or data.get("longitude") is None:
            return Response(
                {"success": False, "errors": {"location": ["latitude and longitude are required."]}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = User.objects.create_user(
            email=admin_email,
            password=data.get("admin_password", "password123"),
            phone_number=data.get("phone", ""),
            role=User.Role.HOSPITAL_ADMIN,
            name=data["name"],
        )
        ensure_profile_bundle(user)

        HospitalProfile.objects.update_or_create(
            user=user,
            defaults={
                "hospital_name": data["name"],
                "address": data.get("address", ""),
                "available_beds": data.get("total_beds", 0),
                "icu_available": data.get("has_icu", False),
                "oxygen_level": HospitalProfile.OxygenLevel.HIGH,
                "services": [],
            },
        )

        location = Point(float(data["longitude"]), float(data["latitude"]), srid=4326)

        hospital = Hospital.objects.create(
            name=data["name"],
            facility_type=data.get("facility_type", Hospital.FacilityType.HOSPITAL),
            address=data.get("address", ""),
            city=data.get("city", ""),
            phone=data.get("phone", ""),
            email=data.get("email", ""),
            admin=user,
            location=location,
            total_beds=data.get("total_beds", 0),
            available_beds=data.get("total_beds", 0),
            total_icu_beds=data.get("total_icu_beds", 0),
            available_icu_beds=data.get("total_icu_beds", 0),
            has_emergency=data.get("has_emergency", False),
            has_icu=data.get("has_icu", False),
            has_surgery=data.get("has_surgery", False),
        )

        return Response(
            {
                "success": True,
                "message": "Hospital registered successfully. Waiting for admin approval.",
                "hospital_id": str(hospital.id),
                "status": "pending",
            },
            status=status.HTTP_201_CREATED,
        )


class HospitalDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Hospital.objects.all()
    serializer_class = HospitalSerializer

    def get_permissions(self):
        if self.request.method == "GET":
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated(), RolePermission()]

    allowed_roles = {"hospital_admin"}

    def get_queryset(self):
        return Hospital.objects.all()

    def retrieve(self, request, pk=None):
        if not settings.GIS_ENABLED:
            return _require_gis_response()

        hospital = get_object_or_404(Hospital, id=pk)
        serializer = HospitalSerializer(hospital)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def update(self, request, pk=None):
        hospital = get_object_or_404(Hospital, id=pk, admin=request.user)
        serializer = HospitalSerializer(hospital, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    def destroy(self, request, pk=None):
        hospital = get_object_or_404(Hospital, id=pk, admin=request.user)
        hospital.delete()
        return Response(
            {"success": True, "message": "Hospital deleted successfully"},
            status=status.HTTP_200_OK,
        )


class HospitalNearbyAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        from django.contrib.gis.measure import D

        if not settings.GIS_ENABLED:
            return _require_gis_response()

        try:
            lat = float(request.query_params.get("latitude"))
            lng = float(request.query_params.get("longitude"))
        except (TypeError, ValueError):
            return Response(
                {"success": False, "errors": {"detail": "latitude and longitude required."}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        radius = float(request.query_params.get("radius", 20))
        user_location = Point(lng, lat, srid=4326)

        hospitals = (
            Hospital.objects.filter(
                is_available=True,
                location__distance_lte=(user_location, D(km=radius)),
            )
            .annotate(distance=Distance("location", user_location))
            .order_by("distance")[:10]
        )

        results = []
        for hospital in hospitals:
            results.append(
                {
                    "id": str(hospital.id),
                    "name": hospital.name,
                    "facility_type": hospital.facility_type,
                    "distance_km": round(hospital.distance.km, 2) if hasattr(hospital, "distance") else None,
                    "available_beds": hospital.available_beds,
                    "has_emergency": hospital.has_emergency,
                }
            )

        return Response({"count": len(results), "results": results}, status=status.HTTP_200_OK)


class HospitalResourceAPIView(APIView):
    def get_permissions(self):
        if self.request.method == "GET":
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated(), RolePermission()]

    allowed_roles = {"hospital_admin"}

    def get(self, request, hospital_id):
        if not settings.GIS_ENABLED:
            return _require_gis_response()

        hospital = get_object_or_404(Hospital, id=hospital_id)
        serializer = HospitalResourceSerializer(hospital)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, hospital_id):
        hospital = get_object_or_404(Hospital, id=hospital_id, admin=request.user)
        serializer = HospitalResourceUpdateSerializer(hospital, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
