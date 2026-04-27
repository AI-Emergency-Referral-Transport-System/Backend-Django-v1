from accounts.models import DriverProfile, HospitalProfile, PatientProfile, Profile, User


def ensure_profile_bundle(user: User) -> Profile:
    profile, _ = Profile.objects.get_or_create(user=user)

    if user.role == User.Role.PATIENT:
        PatientProfile.objects.get_or_create(user=user)
    elif user.role == User.Role.DRIVER:
        DriverProfile.objects.get_or_create(user=user)
    elif user.role == User.Role.HOSPITAL_ADMIN:
        HospitalProfile.objects.get_or_create(user=user)

    return profile

