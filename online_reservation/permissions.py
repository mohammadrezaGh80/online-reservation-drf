from rest_framework.permissions import BasePermission

from .models import Doctor


class IsAdminUserOrDoctorOwner(BasePermission):

    def has_object_permission(self, request, view, obj):
        return bool(
            request.user and request.user.is_authenticated and
            request.user.is_staff or
            getattr(request.user, 'doctor', False) and
            request.user.doctor.status == Doctor.DOCTOR_STATUS_ACCEPTED and
            request.user.doctor == obj
        )
