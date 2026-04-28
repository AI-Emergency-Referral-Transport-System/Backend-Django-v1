from django.conf import settings
from django.contrib.gis.geos import Point
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import DriverProfile, User
from accounts.profiles.services import ensure_profile_bundle
from common.permissions import RolePermission

from .models import Ambulance
from .serializers import (
    AmbulanceSerializer,
    AmbulanceStatusUpdateSerializer,
    DriverCreateSerializer,
)


def _get_managed_hospital(request):
    return getattr(request.user, "managed_hospital", None)


class AmbulanceListCreateAPIView(generics.ListCreateAPIView):
    queryset = Ambulance.objects.select_related("driver", "hospital")
    serializer_class = AmbulanceSerializer
    permission_classes = [RolePermission]
    allowed_roles = {"driver", "hospital_admin"}

    def get_queryset(self):
        if not settings.GIS_ENABLED:
            return Ambulance.objects.none()
        queryset = super().get_queryset()
        status_param = self.request.query_params.get("status")
        if status_param:
            queryset = queryset.filter(status=status_param)
        return queryset


class DriverCreateAPIView(APIView):
    permission_classes = [RolePermission]
    allowed_roles = {"hospital_admin"}

    def post(self, request):
        serializer = DriverCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        managed_hospital = _get_managed_hospital(request)
        if managed_hospital is None:
            return Response(
                {"success": False, "errors": {"detail": ["Hospital profile not found for current admin."]}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        email = data["email"].lower()
        if User.objects.filter(email=email).exists():
            return Response(
                {"success": False, "errors": {"email": ["Email already registered."]}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        ambulance = None
        ambulance_id = data.get("ambulance_id")
        if ambulance_id:
            ambulance = get_object_or_404(Ambulance, id=ambulance_id, hospital=managed_hospital)

        password = "xyz123"
        user = User.objects.create_user(
            email=email,
            password=password,
            phone_number=data.get("phone"),
            role=User.Role.DRIVER,
            is_verified=True,
        )

        profile = ensure_profile_bundle(user)
        profile.full_name = data.get("name", "")
        profile.save()

        driver = user.driver_profile
        driver.license_number = data.get("license_number", "")
        driver.license_expiry = data.get("license_expiry")
        driver.experience_years = data.get("experience_years", 0)
        driver.verification_status = DriverProfile.VerificationStatus.APPROVED
        driver.save()

        if ambulance is not None:
            ambulance.driver = user
            ambulance.save(update_fields=["driver"])

        send_mail(
            subject="Your Driver Account",
            message=f"Your login credentials:\nEmail: {email}\nPassword: {password}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )

        return Response(
            {
                "success": True,
                "message": "Driver account created. Credentials sent via email.",
                "driver": {
                    "id": str(driver.id),
                    "name": data.get("name", ""),
                    "email": email,
                    "license_number": data.get("license_number", ""),
                    "verification_status": driver.verification_status,
                },
                "note": f"Password: {password} (sent to {email})",
            },
            status=status.HTTP_201_CREATED,
        )


class DriverListAPIView(APIView):
    permission_classes = [RolePermission]
    allowed_roles = {"hospital_admin"}

    def get(self, request):
        managed_hospital = _get_managed_hospital(request)
        if managed_hospital is None:
            return Response(
                {"success": True, "hospital": None, "hospital_name": "", "drivers": [], "count": 0},
                status=status.HTTP_200_OK,
            )

        ambulances = Ambulance.objects.filter(
            hospital=managed_hospital,
            driver__isnull=False,
        ).select_related("driver", "driver__profile")

        results = []
        seen_driver_ids = set()
        for ambulance in ambulances:
            driver_user = ambulance.driver
            if driver_user.id in seen_driver_ids:
                continue
            seen_driver_ids.add(driver_user.id)
            driver_profile = getattr(driver_user, "driver_profile", None)
            results.append(
                {
                    "id": str(driver_profile.id) if driver_profile else None,
                    "name": driver_user.full_name,
                    "email": driver_user.email,
                    "phone": driver_user.phone_number,
                    "is_on_duty": driver_profile.is_on_duty if driver_profile else False,
                    "verification_status": (
                        driver_profile.verification_status
                        if driver_profile
                        else DriverProfile.VerificationStatus.PENDING
                    ),
                }
            )

        return Response(
            {
                "success": True,
                "hospital": str(managed_hospital.id),
                "hospital_name": managed_hospital.name,
                "drivers": results,
                "count": len(results),
            },
            status=status.HTTP_200_OK,
        )


class DriverDetailAPIView(APIView):
    permission_classes = [RolePermission]
    allowed_roles = {"hospital_admin"}

    def put(self, request, driver_id):
        managed_hospital = _get_managed_hospital(request)
        driver = get_object_or_404(
            DriverProfile.objects.select_related("user"),
            id=driver_id,
            user__ambulance_profile__hospital=managed_hospital,
        )
        name = request.data.get("name")
        phone = request.data.get("phone")

        if name:
            profile = ensure_profile_bundle(driver.user)
            profile.full_name = name
            profile.save()
        if phone:
            driver.user.phone_number = phone
            driver.user.save(update_fields=["phone_number"])

        return Response(
            {"success": True, "message": "Driver updated successfully"},
            status=status.HTTP_200_OK,
        )

    def delete(self, request, driver_id):
        managed_hospital = _get_managed_hospital(request)
        driver = get_object_or_404(
            DriverProfile,
            id=driver_id,
            user__ambulance_profile__hospital=managed_hospital,
        )
        driver.user.delete()
        return Response(
            {"success": True, "message": "Driver deleted successfully"},
            status=status.HTTP_200_OK,
        )


class AmbulanceCreateAPIView(APIView):
    permission_classes = [RolePermission]
    allowed_roles = {"hospital_admin"}

    def post(self, request):
        managed_hospital = _get_managed_hospital(request)
        if managed_hospital is None:
            return Response(
                {"success": False, "errors": {"detail": ["Hospital profile not found for current admin."]}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        plate = request.data.get("plate_number")
        if Ambulance.objects.filter(plate_number=plate).exists():
            return Response(
                {"success": False, "errors": {"plate_number": ["Already exists."]}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        ambulance = Ambulance.objects.create(
            plate_number=plate,
            ambulance_type=request.data.get("ambulance_type", Ambulance.AmbulanceType.BASIC),
            vehicle_model=request.data.get("vehicle_model", ""),
            phone=request.data.get("phone", ""),
            equipment=request.data.get("equipment", []),
            hospital=managed_hospital,
            organization=managed_hospital.name,
        )

        return Response(
            {
                "success": True,
                "message": "Ambulance created successfully",
                "ambulance": {"id": str(ambulance.id)},
            },
            status=status.HTTP_201_CREATED,
        )


class AmbulanceListAPIView(APIView):
    permission_classes = [RolePermission]
    allowed_roles = {"hospital_admin"}

    def get(self, request):
        managed_hospital = _get_managed_hospital(request)
        ambulances = Ambulance.objects.filter(hospital=managed_hospital).order_by("-created_at")
        results = []
        for ambulance in ambulances:
            results.append(
                {
                    "id": str(ambulance.id),
                    "plate_number": ambulance.plate_number,
                    "status": ambulance.status,
                    "ambulance_type": ambulance.ambulance_type,
                    "vehicle_model": ambulance.vehicle_model,
                }
            )
        return Response(
            {
                "success": True,
                "ambulances": results,
                "count": len(results),
            },
            status=status.HTTP_200_OK,
        )


class DriverDashboardAPIView(APIView):
    permission_classes = [RolePermission]
    allowed_roles = {"driver"}

    def get(self, request):
        driver = DriverProfile.objects.filter(user=request.user).first()
        if not driver:
            return Response(
                {"success": False, "errors": {"detail": "Driver profile not found."}},
                status=status.HTTP_404_NOT_FOUND,
            )

        ambulance = Ambulance.objects.filter(driver=request.user).first()

        return Response(
            {
                "success": True,
                "driver": {
                    "id": str(driver.id),
                    "name": driver.user.full_name,
                    "is_on_duty": driver.is_on_duty,
                },
                "ambulance": (
                    {
                        "id": str(ambulance.id),
                        "plate_number": ambulance.plate_number,
                        "status": ambulance.status,
                    }
                    if ambulance
                    else None
                ),
                "stats": {
                    "today_trips": 0,
                    "completed_trips": driver.completed_trips,
                    "is_online": driver.is_on_duty,
                },
                "active_emergency": None,
            },
            status=status.HTTP_200_OK,
        )


class DriverGoOnlineAPIView(APIView):
    permission_classes = [RolePermission]
    allowed_roles = {"driver"}

    def post(self, request):
        driver = DriverProfile.objects.filter(user=request.user).first()
        if not driver:
            return Response(
                {"success": False, "errors": {"detail": "Driver profile not found."}},
                status=status.HTTP_404_NOT_FOUND,
            )

        is_online = bool(request.data.get("online", True))
        lat = request.data.get("latitude")
        lng = request.data.get("longitude")

        driver.availability = (
            DriverProfile.Availability.ONLINE if is_online else DriverProfile.Availability.OFFLINE
        )
        driver.is_on_duty = is_online
        driver.save(update_fields=["availability", "is_on_duty"])

        ambulance = Ambulance.objects.filter(driver=request.user).first()
        if ambulance:
            ambulance.status = Ambulance.Status.AVAILABLE if is_online else Ambulance.Status.OFFLINE
            update_fields = ["status"]
            if settings.GIS_ENABLED and lat is not None and lng is not None:
                ambulance.current_location = Point(float(lng), float(lat), srid=4326)
                ambulance.last_location_update = timezone.now()
                update_fields.extend(["current_location", "last_location_update"])
            ambulance.save(update_fields=update_fields)

        return Response(
            {
                "success": True,
                "message": "You are now online" if is_online else "You are now offline",
                "driver": {
                    "id": str(driver.id),
                    "is_on_duty": is_online,
                },
                "ambulance": (
                    {"id": str(ambulance.id), "status": ambulance.status}
                    if ambulance
                    else None
                ),
            },
            status=status.HTTP_200_OK,
        )


class DriverLocationAPIView(APIView):
    permission_classes = [RolePermission]
    allowed_roles = {"driver"}

    def post(self, request):
        lat = request.data.get("latitude")
        lng = request.data.get("longitude")
        if lat is None or lng is None:
            return Response(
                {"success": False, "errors": {"detail": "latitude and longitude are required."}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        ambulance = Ambulance.objects.filter(driver=request.user).first()
        if ambulance and settings.GIS_ENABLED:
            ambulance.current_location = Point(float(lng), float(lat), srid=4326)
            ambulance.last_location_update = timezone.now()
            ambulance.save(update_fields=["current_location", "last_location_update"])

        request.user.latitude = float(lat)
        request.user.longitude = float(lng)
        request.user.save(update_fields=["latitude", "longitude"])

        return Response(
            {"success": True, "message": "Location updated"},
            status=status.HTTP_200_OK,
        )


class DriverPendingRequestsAPIView(APIView):
    permission_classes = [RolePermission]
    allowed_roles = {"driver"}

    def get(self, request):
        if not settings.GIS_ENABLED:
            return Response(
                {"success": True, "requests": [], "count": 0},
                status=status.HTTP_200_OK,
            )

        from emergencies.models import Emergency

        ambulance = Ambulance.objects.filter(driver=request.user).select_related("hospital").first()
        pending = Emergency.objects.filter(status=Emergency.Status.PENDING).order_by("-created_at")
        if ambulance and ambulance.hospital_id:
            pending = pending.filter(selected_hospital_id=ambulance.hospital_id)
        pending = pending[:10]

        results = []
        for emergency in pending:
            results.append(
                {
                    "id": str(emergency.id),
                    "emergency_type": emergency.emergency_type,
                    "priority": emergency.priority,
                    "pickup_address": emergency.pickup_address,
                }
            )

        return Response(
            {"success": True, "requests": results, "count": len(results)},
            status=status.HTTP_200_OK,
        )


class DriverAcceptEmergencyAPIView(APIView):
    permission_classes = [RolePermission]
    allowed_roles = {"driver"}

    def post(self, request, emergency_id):
        if not settings.GIS_ENABLED:
            return Response(
                {"success": False, "errors": {"detail": "GIS required."}},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        from emergencies.models import Emergency

        ambulance = get_object_or_404(Ambulance, driver=request.user)
        emergency = get_object_or_404(Emergency, id=emergency_id)

        if emergency.assigned_ambulance_id is not None:
            return Response(
                {"success": False, "errors": {"detail": "Emergency already accepted."}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        emergency.assigned_ambulance = ambulance
        emergency.status = Emergency.Status.ACCEPTED
        emergency.dispatched_at = timezone.now()
        emergency.save(update_fields=["assigned_ambulance", "status", "dispatched_at"])

        ambulance.status = Ambulance.Status.EN_ROUTE
        ambulance.save(update_fields=["status"])

        return Response(
            {"success": True, "message": "Emergency accepted"},
            status=status.HTTP_200_OK,
        )


class DriverEmergencyActionAPIView(APIView):
    permission_classes = [RolePermission]
    allowed_roles = {"driver"}

    def post(self, request, emergency_id):
        if not settings.GIS_ENABLED:
            return Response(
                {"success": False, "errors": {"detail": "GIS required."}},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        from emergencies.models import Emergency

        action = request.data.get("action")
        emergency = get_object_or_404(Emergency, id=emergency_id, assigned_ambulance__driver=request.user)
        ambulance = emergency.assigned_ambulance

        if action == "arrived":
            emergency.status = Emergency.Status.DRIVER_ARRIVED
            ambulance.status = Ambulance.Status.BUSY
            ambulance.save(update_fields=["status"])
            emergency.save(update_fields=["status"])
        elif action == "picked_up":
            emergency.status = Emergency.Status.RETRIEVED
            emergency.save(update_fields=["status"])
        elif action == "en_route_hospital":
            emergency.status = Emergency.Status.GOING_TO_HOSPITAL
            emergency.save(update_fields=["status"])
        elif action == "arrived_hospital":
            emergency.status = Emergency.Status.DELIVERED
            emergency.save(update_fields=["status"])
        elif action == "complete":
            emergency.mark_completed()
            if ambulance:
                ambulance.status = Ambulance.Status.AVAILABLE
                ambulance.save(update_fields=["status"])
        else:
            return Response(
                {"success": False, "errors": {"action": ["Invalid action."]}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {"success": True, "message": f"Action '{action}' completed"},
            status=status.HTTP_200_OK,
        )


class AmbulanceStatusUpdateAPIView(APIView):
    permission_classes = [RolePermission]
    allowed_roles = {"driver", "hospital_admin"}

    def put(self, request, pk):
        ambulance = get_object_or_404(Ambulance, id=pk)
        serializer = AmbulanceStatusUpdateSerializer(ambulance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save(last_location_update=timezone.now())
        return Response(serializer.data, status=status.HTTP_200_OK)
