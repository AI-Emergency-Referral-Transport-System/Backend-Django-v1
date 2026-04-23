from django.contrib import admin

from accounts.models import DriverProfile, HospitalProfile, OTPCode, Profile, User


admin.site.register(User)
admin.site.register(Profile)
admin.site.register(DriverProfile)
admin.site.register(HospitalProfile)
admin.site.register(OTPCode)
