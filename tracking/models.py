from django.contrib.gis.db import models

from ambulances.models import Ambulance
from common.models import TimestampedUUIDModel
from emergencies.models import Emergency


class Location_Track(TimestampedUUIDModel):
    # Link to the specific mission/emergency
    emergency = models.ForeignKey(Emergency, on_delete=models.CASCADE, related_name='location_history')
    ambulance = models.ForeignKey(Ambulance, on_delete=models.CASCADE)
    coordinates = models.PointField(srid=4326)
    speed = models.FloatField(null=True, blank=True)
    heading = models.FloatField(null=True, blank=True)
    accuracy = models.FloatField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"Tracking for {self.emergency.id} at {self.timestamp}"


class RoutePoint(TimestampedUUIDModel):
    emergency = models.ForeignKey(Emergency, on_delete=models.CASCADE, related_name="route_points")
    latitude = models.FloatField()
    longitude = models.FloatField()
    sequence = models.PositiveIntegerField(default=0)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["sequence", "timestamp"]

    def __str__(self):
        return f"RoutePoint<{self.emergency_id}:{self.sequence}>"

