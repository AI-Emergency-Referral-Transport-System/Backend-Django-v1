from django.contrib.gis.db import models 
from emergencies.models import Emergency
from ambulances.models import Ambulance

class Location_Track(models.Model):
    # Link to the specific mission/emergency
    emergency = models.ForeignKey(Emergency, on_delete=models.CASCADE, related_name='location_history')
    ambulance = models.ForeignKey(Ambulance, on_delete=models.CASCADE)
    
    
    coordinates = models.PointField(srid=4326)
    
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"Tracking for {self.emergency.id} at {self.timestamp}"

