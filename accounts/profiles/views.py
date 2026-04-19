from django.contrib.auth import get_user_model
from rest_framework import generics, permissions

from accounts.permissions import RolePermission
from accounts.profiles.serializers import ProfileSerializer
from accounts.profiles.services import ensure_profile_bundle


User = get_user_model()


class ProfileRetrieveUpdateAPIView(generics.RetrieveUpdateAPIView):
    permission_classes = [permissions.IsAuthenticated, RolePermission]
    serializer_class = ProfileSerializer
    allowed_roles = {
        User.Role.PATIENT,
        User.Role.DRIVER,
        User.Role.HOSPITAL_ADMIN,
    }

    def get_object(self):
        return ensure_profile_bundle(self.request.user)
