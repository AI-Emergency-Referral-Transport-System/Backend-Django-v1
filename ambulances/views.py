from django.shortcuts import get_object_or_404
from django.utils import timezone

from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response

from .models import Ambulance
from .serializers import AmbulanceSerializer, AmbulanceStatusUpdateSerializer
from common.permissions import RolePermission
from emergencies.models import Emergency


class AmbulanceListCreateAPIView(generics.ListCreateAPIView):
    queryset = Ambulance.objects.select_related("driver", "hospital")
    serializer_class = AmbulanceSerializer
    permission_classes = [RolePermission]
    allowed_roles = {"driver", "hospital_admin"}

    def get_queryset(self):
        #  Be able to filter available ambulances
        queryset = super().get_queryset()
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)
        return queryset


class DriverAcceptEmergencyAPIView(APIView):
    permission_classes = [RolePermission]
    allowed_roles = {"driver"}

    def post(self, request, emergency_id):
        ambulance = get_object_or_404(Ambulance, driver=request.user)
        emergency = get_object_or_404(Emergency, id=emergency_id)

        if emergency.assigned_ambulance_id is not None:
            return Response({"detail": "Emergency already accepted."}, status=status.HTTP_400_BAD_REQUEST)

        emergency.assigned_ambulance = ambulance
        emergency.status = Emergency.Status.ACCEPTED
        emergency.save(update_fields=["assigned_ambulance", "status"])

        ambulance.status = Ambulance.Status.EN_ROUTE
        ambulance.save(update_fields=["status"])

        return Response({"detail": "Emergency accepted."}, status=status.HTTP_200_OK)


class AmbulanceStatusUpdateAPIView(APIView):
    permission_classes = [RolePermission]
    allowed_roles = {"driver", "hospital_admin"}

    def put(self, request, pk):
        ambulance = get_object_or_404(Ambulance, id=pk)
        serializer = AmbulanceStatusUpdateSerializer(ambulance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save(last_location_update=timezone.now())
        return Response(serializer.data, status=status.HTTP_200_OK)
