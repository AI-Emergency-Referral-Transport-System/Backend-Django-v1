from django.conf import settings
from django.shortcuts import get_object_or_404
from django.utils import timezone

from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions

from .models import Ambulance, Driver
from .serializers import AmbulanceSerializer, AmbulanceStatusUpdateSerializer, DriverCreateSerializer
from common.permissions import RolePermission


class AmbulanceListCreateAPIView(generics.ListCreateAPIView):
    queryset = Ambulance.objects.select_related("driver", "hospital")
    serializer_class = AmbulanceSerializer
    permission_classes = [RolePermission]
    allowed_roles = {"driver", "hospital_admin"}

    def get_queryset(self):
        if not settings.GIS_ENABLED:
            return Ambulance.objects.none()
        queryset = super().get_queryset()
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)
        return queryset


# Hospital Admin - Driver Management
class DriverCreateAPIView(APIView):
    permission_classes = [RolePermission]
    allowed_roles = {"hospital_admin"}

    def post(self, request):
        serializer = DriverCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        from accounts.models import User

        email = data.get("email")
        if User.objects.filter(email=email).exists():
            return Response(
                {"success": False, "errors": {"email": ["Email already registered."]}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        password = "xyz123"
        user = User.objects.create_user(
            email=email,
            password=password,
            phone_number=data.get("phone"),
            role=User.Role.DRIVER,
        )

        driver = Driver.objects.create(
            user=user,
            license_number=data.get("license_number", ""),
        )

        from django.core.mail import send_mail

        send_mail(
            subject="Your Driver Account",
            message=f"Your login credentials:\nEmail: {email}\nPassword: {password}",
            from_email="no-reply@ai-emergency.local",
            recipient_list=[email],
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
                    "verification_status": "approved",
                },
                "note": f"Password: {password} (sent to {email})",
            },
            status=status.HTTP_201_CREATED,
        )


class DriverListAPIView(APIView):
    permission_classes = [RolePermission]
    allowed_roles = {"hospital_admin"}

    def get(self, request):
        drivers = Driver.objects.select_related("user").order_by("-created_at")
        results = []
        for d in drivers:
            results.append(
                {
                    "id": str(d.id),
                    "name": d.user.profile.full_name if d.user.profile else "",
                    "email": d.user.email,
                    "phone": d.user.phone_number,
                    "is_on_duty": d.availability == "online",
                    "verification_status": d.verification_status,
                }
            )
        return Response(
            {
                "success": True,
                "hospital": None,
                "hospital_name": "",
                "drivers": results,
                "count": len(results),
            },
            status=status.HTTP_200_OK,
        )


class DriverDetailAPIView(APIView):
    permission_classes = [RolePermission]
    allowed_roles = {"hospital_admin"}

    def put(self, request, driver_id):
        driver = get_object_or_404(Driver, id=driver_id)
        name = request.data.get("name")
        phone = request.data.get("phone")

        if name and driver.user.profile:
            driver.user.profile.full_name = name
            driver.user.profile.save()
        if phone:
            driver.user.phone_number = phone
            driver.user.save()

        return Response(
            {"success": True, "message": "Driver updated successfully"},
            status=status.HTTP_200_OK,
        )

    def delete(self, request, driver_id):
        driver = get_object_or_404(Driver, id=driver_id)
        driver.user.delete()
        return Response(
            {"success": True, "message": "Driver deleted successfully"},
            status=status.HTTP_200_OK,
        )


# Ambulance Management
class AmbulanceCreateAPIView(APIView):
    permission_classes = [RolePermission]
    allowed_roles = {"hospital_admin"}

    def post(self, request):
        plate = request.data.get("plate_number")
        if Ambulance.objects.filter(plate_number=plate).exists():
            return Response(
                {"success": False, "errors": {"plate_number": ["Already exists."]}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        ambulance = Ambulance.objects.create(
            plate_number=plate,
            organization=request.data.get("vehicle_model", ""),
            phone=request.data.get("phone", ""),
            equipment=request.data.get("equipment", []),
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
        ambulances = Ambulance.objects.order_by("-created_at")
        results = []
        for a in ambulances:
            results.append(
                {
                    "id": str(a.id),
                    "plate_number": a.plate_number,
                    "status": a.status,
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


# Driver App Endpoints
class DriverDashboardAPIView(APIView):
    permission_classes = [RolePermission]
    allowed_roles = {"driver"}

    def get(self, request):
        driver = Driver.objects.filter(user=request.user).first()
        if not driver:
            return Response(
                {"success": False, "errors": {"detail": "Driver profile not found."}},
                status=status.HTTP_404_NOT_FOUND,
            )

        ambulance = getattr(driver, "ambulance", None)

        return Response(
            {
                "success": True,
                "driver": {
                    "id": str(driver.id),
                    "name": driver.user.profile.full_name if driver.user.profile else "",
                    "is_on_duty": driver.availability == "online",
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
                    "completed_trips": 0,
                    "is_online": driver.availability == "online",
                },
                "active_emergency": None,
            },
            status=status.HTTP_200_OK,
        )


class DriverGoOnlineAPIView(APIView):
    permission_classes = [RolePermission]
    allowed_roles = {"driver"}

    def post(self, request):
        driver = Driver.objects.filter(user=request.user).first()
        if not driver:
            return Response(
                {"success": False, "errors": {"detail": "Driver profile not found."}},
                status=status.HTTP_404_NOT_FOUND,
            )

        is_online = request.data.get("online", True)
        lat = request.data.get("latitude")
        lng = request.data.get("longitude")

        driver.availability = "online" if is_online else "offline"
        driver.save()

        return Response(
            {
                "success": True,
                "message": "You are now online" if is_online else "You are now offline",
                "driver": {
                    "id": str(driver.id),
                    "is_on_duty": is_online,
                },
                "ambulance": (
                    {"id": str(driver.ambulance.id), "status": driver.ambulance.status}
                    if hasattr(driver, "ambulance") and driver.ambulance
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

        pending = Emergency.objects.filter(
            status=Emergency.Status.PENDING,
        ).order_by("-created_at")[:10]

        results = []
        for e in pending:
            results.append(
                {
                    "id": str(e.id),
                    "emergency_type": e.emergency_type,
                    "priority": e.priority,
                    "pickup_address": "",
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

        ambulance = get_object_or_404(Ambulance, driver=request.user)
        emergency = get_object_or_404(Emergency, id=emergency_id)

        if emergency.assigned_ambulance_id is not None:
            return Response(
                {"success": False, "errors": {"detail": "Emergency already accepted."}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        emergency.assigned_ambulance = ambulance
        emergency.status = Emergency.Status.ACCEPTED
        emergency.save(update_fields=["assigned_ambulance", "status"])

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

        action = request.data.get("action")
        emergency = get_object_or_404(Emergency, id=emergency_id)

        if action == "arrived":
            emergency.status = Emergency.Status.ACCEPTED
        elif action == "picked_up":
            emergency.status = Emergency.Status.RETRIEVED
        elif action == "en_route_hospital":
            emergency.status = Emergency.Status.IN_PROGRESS
        elif action == "arrived_hospital":
            emergency.status = Emergency.Status.IN_PROGRESS
        elif action == "complete":
            emergency.status = Emergency.Status.DELIVERED

        emergency.save()
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