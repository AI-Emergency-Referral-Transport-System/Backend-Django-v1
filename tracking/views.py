from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

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