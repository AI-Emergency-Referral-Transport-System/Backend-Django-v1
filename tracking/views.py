from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from django.db import transaction
from django.shortcuts import get_object_or_404
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from accounts.permissions import RolePermission
from accounts.models import User
from ambulances.models import Ambulance
from emergencies.models import Emergency
from hospitals.models import Hospital
from tracking.serializers import EmergencySerializer

class CreateEmergencyAPIView(APIView):
    """
    Only Patients can trigger a new emergency request.
    """
    permission_classes = [permissions.IsAuthenticated, RolePermission]
    allowed_roles = {User.Role.DRIVER, User.Role.PATIENT}

    @transaction.atomic
    def post(self, request, hospital_id):
        lat = request.data.get('lat')
        lon = request.data.get('lon')

        if not lat or not lon:
            return Response({"error": "Coordinates required"}, status=status.HTTP_400_BAD_REQUEST)

        patient_coords = Point(float(lon), float(lat), srid=4326)
        
        hospital = Hospital.objects.get(id=hospital_id)

        # Using request.user (The actual authenticated patient)
        emergency = Emergency.objects.create(
            patient=request.user,
            patient_location=patient_coords,
            selected_hospital=hospital,
            status='pending'
        )
        
        # Use the serializer to return the created emergency data
        serializer = EmergencySerializer(emergency)

        # Notify nearby ambulances
        nearby_ambulances = Ambulance.objects.filter(
            status='available',
            current_location__distance_lte=(patient_coords, D(km=20))
        )

        channel_layer = get_channel_layer()
        for ambulance in nearby_ambulances:
            async_to_sync(channel_layer.group_send)(
                f"ambulance_driver_{ambulance.id}", 
                {
                    "type": "new_emergency_alert",
                    "data": {
                        "emergency_id": str(emergency.id), # UUID friendly
                        "patient_lat": lat,
                        "patient_lon": lon,
                        "emergency_data": serializer.data, # Send the full serialized data for convenience
                    }
                }
            )

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class AcceptEmergencyAPIView(APIView):
    """
    Only Drivers can accept an emergency.
    """
    permission_classes = [permissions.IsAuthenticated, RolePermission]
    allowed_roles = {User.Role.DRIVER}

    @transaction.atomic
    def post(self, request, ambulance_id, emergency_id):
        # select_for_update prevents race conditions
        emergency = Emergency.objects.select_for_update().get(id=emergency_id)

        if emergency.assigned_ambulance is not None:
            return Response({"error": "Already accepted by another driver."}, status=status.HTTP_400_BAD_REQUEST)

        ambulance = Ambulance.objects.get(id=ambulance_id)
        
        # Verify the driver owns this ambulance record
        # (Optional: check if ambulance.driver == request.user)

        emergency.assigned_ambulance = ambulance
        emergency.status = 'accepted'
        emergency.save()

        ambulance.status = 'on_duty'
        ambulance.save()

        # Notify the patient room
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"emergency_{emergency_id}",
            {
                "type": "assignment_notification",
                "ambulance_id": ambulance.id,
                "plate_number": ambulance.plate_number,
                "status": "Ambulance En Route"
            }
        )

        return Response({
            "status": "success",
            "patient_lat": emergency.patient_location.y,
            "patient_lon": emergency.patient_location.x,
        })
    
class AcceptEmergencyAPIView(APIView):
    """
    Only Drivers can accept an emergency.
    """
    permission_classes = [permissions.IsAuthenticated, RolePermission]
    allowed_roles = {User.Role.DRIVER}

    @transaction.atomic
    def post(self, request, ambulance_id, emergency_id):
        # select_for_update prevents race conditions
        emergency = Emergency.objects.select_for_update().get(id=emergency_id)

        if emergency.assigned_ambulance is not None:
            return Response({"error": "Already accepted by another driver."}, status=status.HTTP_400_BAD_REQUEST)

        ambulance = Ambulance.objects.get(id=ambulance_id)
        
        # Verify the driver owns this ambulance record
        # (Optional: check if ambulance.driver == request.user)

        emergency.assigned_ambulance = ambulance
        emergency.status = 'accepted'
        emergency.save()

        ambulance.status = 'on_duty'
        ambulance.save()

        # Notify the patient room
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"emergency_{emergency_id}",
            {
                "type": "assignment_notification",
                "ambulance_id": ambulance.id,
                "plate_number": ambulance.plate_number,
                "status": "Ambulance En Route"
            }
        )

        return Response({
            "status": "success",
            "patient_lat": emergency.patient_location.y,
            "patient_lon": emergency.patient_location.x,
        })
    
class PickupPatientAPIView(APIView):
    """
    Update status when driver arrives at patient.
    Only the assigned DRIVER can call this.
    """
    permission_classes = [permissions.IsAuthenticated, RolePermission]
    allowed_roles = {User.Role.DRIVER}

    def post(self, request, emergency_id):
        # 1. Fetch the emergency or return 404
        emergency = get_object_or_404(Emergency, id=emergency_id)

        # 2. Security Check: Is this the driver assigned to this mission?
        if emergency.assigned_ambulance.driver != request.user:
            return Response(
                {"error": "You are not authorized to update this mission."},
                status=status.HTTP_403_FORBIDDEN
            )

        # 3. Business Logic
        emergency.status = 'retrieved'
        emergency.save()
        
        return Response({
            "status": "success",
            "hospital_name": emergency.selected_hospital.name,
            "hospital_lat": emergency.selected_hospital.location.y,
            "hospital_lon": emergency.selected_hospital.location.x,
        }, status=status.HTTP_200_OK)


class CompleteMissionAPIView(APIView):
    """
    Finalize mission when patient is delivered to hospital.
    Only the assigned DRIVER can call this.
    """
    permission_classes = [permissions.IsAuthenticated, RolePermission]
    allowed_roles = {User.Role.DRIVER}

    def post(self, request, emergency_id):
        emergency = get_object_or_404(Emergency, id=emergency_id)

        # Security Check
        if emergency.assigned_ambulance.driver != request.user:
            return Response(
                {"error": "Unauthorized action."},
                status=status.HTTP_403_FORBIDDEN
            )

        # Business Logic: Use an atomic transaction if you have multiple DB updates
        emergency.is_resolved = True
        emergency.status = 'completed' # Good for history tracking
        emergency.save()

        # Update Ambulance Status
        ambulance = emergency.assigned_ambulance
        ambulance.status = 'available'
        ambulance.save()

        return Response({"status": "mission_completed"}, status=status.HTTP_200_OK)

def assign_hospital_to_emergency(emergency, hospital):
    # ... your existing assignment logic ...
    
    # TRIGGER THE WEBSOCKET ALERT
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f'hospital_{hospital.id}', # The group we created in the Consumer
        {
            'type': 'new_emergency_alert',
            'emergency_id': str(emergency.id),
            'patient_name': emergency.patient.name,
        }
    )
