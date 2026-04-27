from django.contrib import admin

from accounts.models import (
    DriverProfile,
    EmergencyContact,
    HospitalProfile,
    OTPCode,
    PatientProfile,
    Profile,
    User,
)


admin.site.register(User)
admin.site.register(Profile)
admin.site.register(PatientProfile)
admin.site.register(EmergencyContact)
admin.site.register(DriverProfile)
admin.site.register(HospitalProfile)
admin.site.register(OTPCode)
