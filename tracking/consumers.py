import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.gis.geos import Point
from .models import Location_Track
from emergencies.models import Emergency

class AmbulanceTrackingConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # The URL contains the emergency ID (e.g., ws/track/15/)
        self.emergency_id = self.scope['url_route']['kwargs']['emergency_id']
        self.room_group_name = f'emergency_{self.emergency_id}'

        # Join the specific mission group
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    # Receive GPS data from the DRIVER app
    async def receive(self, text_data):
        data = json.loads(text_data)
        lat = data.get('lat')
        lon = data.get('lon')

        if lat and lon:
            # 1. Update the database (Save history in Location_Track)
            await self.record_movement(lat, lon)

            # 2. Broadcast the update to the PATIENT and HOSPITAL apps in the group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'ambulance_location_update',
                    'lat': lat,
                    'lon': lon,
                }
            )

    @database_sync_to_async
    def record_movement(self, lat, lon):
        # Fulfills Task 2: Save real-time movement to the database
        try:
            emergency = Emergency.objects.get(id=self.emergency_id)
            Location_Track.objects.create(
                emergency=emergency,
                ambulance=emergency.ambulance,
                latitude=lat,
                longitude=lon
            )
        except Emergency.DoesNotExist:
            pass

    # This method sends the broadcasted data to everyone in the room
    async def ambulance_location_update(self, event):
        await self.send(text_data=json.dumps({
            'lat': event['lat'],
            'lon': event['lon'],
            'emergency_id': self.emergency_id
        }))