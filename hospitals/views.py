from django.contrib.gis.geos import Point
from django.contrib.gis.db.models.functions import Distance
from django.shortcuts import get_object_or_404
from django.conf import settings

from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from common.permissions import RolePermission
from hospitals.serializers import (
    HospitalListSerializer,
    HospitalRegistrationSerializer,
    HospitalResourceSerializer,
    HospitalResourceUpdateSerializer,
    HospitalSerializer,
)


class HospitalRootAPIView(APIView):
    permission_classes = [RolePermission]
    allowed_roles = {"patient", "driver", "hospital_admin"}

    def get(self, request):
        return Response(
            {
                "message": "Hospitals API is available.",
                "endpoints": {
                    "list": "/api/v1/hospitals/",
                    "register": "/api/v1/hospitals/register/",
                    "nearby": "/api/v1/hospitals/nearby/",
                    "resources": "/api/v1/hospitals/{id}/resources/",
                },
            },
            status=status.HTTP_200_OK,
        )


class HospitalListCreateAPIView(generics.ListCreateAPIView):
    queryset = None
    serializer_class = HospitalListSerializer
    permission_classes = [RolePermission]
    allowed_roles = {"patient", "driver", "hospital_admin"}

    def get_queryset(self):
        from hospitals.models import Hospital

        if not settings.GIS_ENABLED:
            return Response(
                {"error": "Hospitals not available - GDAL required."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        return Hospital.objects.all()

    def list(self, request):
        from hospitals.models import Hospital

        queryset = Hospital.objects.all()
        city = request.query_params.get("city")
        specialty = request.query_params.get("specialty")
        search = request.query_params.get("search")

        if city:
            queryset = queryset.filter(address__icontains=city)
        if specialty == "emergency":
            queryset = queryset.filter(has_trauma=True)
        if search:
            queryset = queryset.filter(name__icontains=search) | queryset.filter(
                address__icontains=search
            )

        serializer = HospitalListSerializer(queryset, many=True)
        return Response(
            {"count": queryset.count(), "results": serializer.data},
            status=status.HTTP_200_OK,
        )

    def create(self, request):
        from hospitals.models import Hospital
        from accounts.models import User, HospitalProfile

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

        user = User.objects.create_user(
            email=admin_email,
            password=data.get("admin_password", "password123"),
            role=User.Role.HOSPITAL_ADMIN,
        )

        HospitalProfile.objects.create(
            user=user,
            hospital_name=data["name"],
            address=data.get("address", ""),
            available_beds=data.get("total_beds", 0),
        )

        location = None
        if data.get("latitude") and data.get("longitude"):
            location = Point(data["longitude"], data["latitude"], srid=4326)

        hospital = Hospital.objects.create(
            name=data["name"],
            phone=data.get("phone", ""),
            admin=user,
            location=location,
            available_beds=data.get("total_beds", 0),
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
    queryset = None
    serializer_class = HospitalSerializer
    permission_classes = [RolePermission]
    allowed_roles = {"hospital_admin"}

    def get_queryset(self):
        from hospitals.models import Hospital

        return Hospital.objects.all()

    def retrieve(self, request, pk=None):
        from hospitals.models import Hospital
        from django.shortcuts import get_object_or_404

        hospital = get_object_or_404(Hospital, id=pk)
        serializer = HospitalSerializer(hospital)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def update(self, request, pk=None):
        from hospitals.models import Hospital
        from django.shortcuts import get_object_or_404

        hospital = get_object_or_404(Hospital, id=pk)
        serializer = HospitalSerializer(hospital, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    def destroy(self, request, pk=None):
        from hospitals.models import Hospital
        from django.shortcuts import get_object_or_404

        hospital = get_object_or_404(Hospital, id=pk)
        hospital.delete()
        return Response(
            {"success": True, "message": "Hospital deleted successfully"},
            status=status.HTTP_200_OK,
        )


class HospitalNearbyAPIView(APIView):
    permission_classes = [RolePermission]
    allowed_roles = {"patient", "driver", "hospital_admin"}

    def get(self, request):
        from django.contrib.gis.measure import D
        from hospitals.models import Hospital

        if not settings.GIS_ENABLED:
            return Response(
                {"error": "Nearby hospitals not available - GDAL required."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

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
        for h in hospitals:
            results.append(
                {
                    "id": str(h.id),
                    "name": h.name,
                    "facility_type": "hospital",
                    "distance_km": round(h.distance.km, 2) if hasattr(h, "distance") else None,
                    "available_beds": h.available_beds,
                    "has_emergency": h.has_trauma,
                }
            )

        return Response({"count": len(results), "results": results}, status=status.HTTP_200_OK)


class HospitalResourceAPIView(APIView):
    permission_classes = [RolePermission]
    allowed_roles = {"hospital_admin"}

    def get(self, request, hospital_id):
        from hospitals.models import Hospital
        from django.shortcuts import get_object_or_404

        hospital = get_object_or_404(Hospital, id=hospital_id)
        serializer = HospitalResourceSerializer(hospital)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, hospital_id):
        from hospitals.models import Hospital
        from django.shortcuts import get_object_or_404

        hospital = get_object_or_404(Hospital, id=hospital_id)
        serializer = HospitalResourceUpdateSerializer(hospital, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)