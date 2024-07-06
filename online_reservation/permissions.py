from django.utils.translation import gettext as _
from rest_framework.permissions import BasePermission
from rest_framework.exceptions import PermissionDenied

from .models import Doctor


class IsDoctor(BasePermission):

    def has_permission(self, request, view):
        return bool(
            request.user and request.user.is_authenticated and
            getattr(request.user, 'doctor', False) and request.user.doctor.status == Doctor.DOCTOR_STATUS_ACCEPTED
        )

class IsPatientInfoComplete(BasePermission):

    def has_permission(self, request, view):
        fields = ['first_name', 'last_name', 'birth_date', 'gender', 'province', 'city']
        patient = request.user.patient

        for field in fields:
            if not getattr(patient, field, False):
                raise PermissionDenied(detail=_('To register a comment, you must first complete your personal information in your profile.'))
        
        if not getattr(patient, 'is_foreign_national', False) and not getattr(patient, 'national_code', False):
            raise PermissionDenied(detail=_('To register a comment, you must first complete your personal information in your profile.'))
        
        return True
