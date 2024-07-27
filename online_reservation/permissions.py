from django.utils.translation import gettext as _
from rest_framework.permissions import BasePermission
from rest_framework.exceptions import PermissionDenied

from .models import Doctor, Person


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
                raise PermissionDenied(detail=_('You must first complete your personal information in your profile.'))
        
        if not getattr(patient, 'is_foreign_national', False) and not getattr(patient, 'national_code', False):
            raise PermissionDenied(detail=_('You must first complete your personal information in your profile.'))
        
        return True


class IsDoctorOfficeAddressInfoComplete(BasePermission):

    def has_permission(self, request, view):
        fields = ['province', 'city', 'office_address']
        doctor = request.user.doctor

        for field in fields:
            if not getattr(doctor, field, False):
                raise PermissionDenied(detail=_('To register a reserve, you must first complete your office address information in your profile.'))
        
        return True
    

class IsDoctorOfficeAddressInfoCompleteForAdmin(BasePermission):

    def has_permission(self, request, view):
        fields = ['province', 'city', 'office_address']
        context = view.get_serializer_context()
        doctor = context.get('doctor')

        for field in fields:
            if not getattr(doctor, field, False):
                raise PermissionDenied(
                    detail=_('To register a reserve for %(doctor_full_name)s, you must first complete %(doctor_gender)s office address information.') % 
                    {'doctor_full_name': doctor.full_name,
                     'doctor_gender': 'his' if doctor.gender == Person.PERSON_GENDER_MALE else 'her'}
                )
        
        return True
