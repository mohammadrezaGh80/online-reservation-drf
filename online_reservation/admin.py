from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from datetime import datetime, timezone

from . import models


@admin.register(models.Province)
class ProvinceAdmin(admin.ModelAdmin):
    list_display = ['name']
    list_per_page = 15
    search_fields = ['name']


@admin.register(models.City)
class CityAdmin(admin.ModelAdmin):
    list_display = ['name', 'province']
    list_per_page = 15
    search_fields = ['name']
    list_select_related = ['province']


@admin.register(models.Insurance)
class InsuranceAdmin(admin.ModelAdmin):
    list_display = ['name']
    list_per_page = 15
    search_fields = ['name']


@admin.register(models.Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ['first_name', 'last_name', 'get_phone', 'gender', 'insurance', 'is_foreign_national', 'province', 'city']
    list_per_page = 15
    list_select_related = ['insurance', 'province', 'city', 'user']
    search_fields = ['first_name', 'last_name', 'user__phone']
    autocomplete_fields = ['user', 'insurance', 'province', 'city']
    ordering = ['-created_datetime']

    @admin.display(description=_('phone'))
    def get_phone(self, patient):
        return patient.user.phone


@admin.register(models.Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ['first_name', 'last_name', 'medical_council_number', 'get_phone', 'gender', 'status', 'province', 'city']
    list_per_page = 15
    list_select_related = ['province', 'city', 'user']
    search_fields = ['first_name', 'last_name']
    autocomplete_fields = ['user', 'province', 'city']
    ordering = ['-confirm_datetime']

    @admin.display(description=_('phone'))
    def get_phone(self, patient):
        return patient.user.phone


@admin.register(models.Specialty)
class SpecialtyAdmin(admin.ModelAdmin):
    list_display = ['name']
    list_per_page = 15
    search_fields = ['name']


@admin.register(models.DoctorSpecialty)
class DoctorSpecialtyAdmin(admin.ModelAdmin):
    list_display = ['get_full_name', 'specialty']
    list_per_page = 15
    search_fields = ['doctor__first_name', 'doctor__last_name', 'specialty__name']
    autocomplete_fields = ['doctor', 'specialty']
    list_select_related = ['doctor', 'specialty']

    @admin.display(description=_('full_name'))
    def get_full_name(self, doctor_specialty):
        return doctor_specialty.doctor.full_name


@admin.register(models.Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['patient', 'get_doctor', 'rating', 'is_suggest', 'is_anonymous']
    list_per_page = 15
    list_select_related = ['patient', 'doctor']
    autocomplete_fields = ['patient', 'doctor']
    ordering = ['-created_datetime']

    @admin.display(description=_('doctor'))
    def get_doctor(self, comment):
        return comment.doctor.full_name


@admin.register(models.Reserve)
class ReserveAdmin(admin.ModelAdmin):
    list_display = ['patient', 'get_doctor', 'status', 'price', 'get_reserve_datetime', 'is_expired']
    list_per_page = 15
    list_select_related = ['patient', 'doctor']
    autocomplete_fields = ['patient', 'doctor']
    ordering = ['-reserve_datetime']

    @admin.display(description=_('doctor'))
    def get_doctor(self, reserve):
        return reserve.doctor.full_name
    
    @admin.display(description=_('reserve_datetime'))
    def get_reserve_datetime(self, reserve):
        return reserve.reserve_datetime.strftime('%Y-%m-%d %H:%M:%S')
    
    @admin.display(description=_('is_expired'))
    def is_expired(self, reserve):
        return True if reserve.reserve_datetime < datetime.now(timezone.utc) else False
