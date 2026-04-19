from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import Ambulance
from .serializers import AmbulanceSerializer
from common.permissions import RolePermission


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
