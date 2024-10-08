from typing import Any
from django.contrib import admin
from django.db.models import Count
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.utils.http import urlencode
from django.utils.html import format_html

from datetime import datetime, timezone, timedelta

from . import models


TEHRAN_TZ = timezone(timedelta(hours=3, minutes=30))


# Inlines
class DoctorSpecialtyInline(admin.TabularInline):
    model = models.DoctorSpecialty
    extra = 1


# Model Admins
@admin.register(models.Province)
class ProvinceAdmin(admin.ModelAdmin):
    list_display = ['name', 'num_of_cities']
    list_per_page = 15
    search_fields = ['name']

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(cities_count=Count('cities'))

    @admin.display(description=_('# cities'), ordering='cities_count')
    def num_of_cities(self, province):
        url = (
            reverse('admin:online_reservation_city_changelist')
            + '?'
            + urlencode({
                'province': province.id
            })
        )

        return format_html('<a href={}>{}</a>', url, province.cities_count)


@admin.register(models.City)
class CityAdmin(admin.ModelAdmin):
    list_display = ['name', 'province']
    list_per_page = 15
    search_fields = ['name']
    autocomplete_fields = ['province']
    list_select_related = ['province']


@admin.register(models.Insurance)
class InsuranceAdmin(admin.ModelAdmin):
    list_display = ['name', 'num_of_doctors', 'num_of_patients']
    list_per_page = 15
    search_fields = ['name']

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            doctors_count=Count('doctors', distinct=True), patients_count=Count('patients', distinct=True)
        )
    
    @admin.display(description=_('# doctors'), ordering='doctors_count')
    def num_of_doctors(self, insurance):
        url = (
            reverse('admin:online_reservation_doctorinsurance_changelist')
            + '?'
            + urlencode({
                'insurance': insurance.id
            })
        )

        return format_html('<a href={}>{}</a>', url, insurance.doctors_count)
    
    @admin.display(description=_('# patients'), ordering='patients_count')
    def num_of_patients(self, insurance):
        url = (
            reverse('admin:online_reservation_patient_changelist')
            + '?'
            + urlencode({
                'insurance': insurance.id
            })
        )

        return format_html('<a href={}>{}</a>', url, insurance.patients_count)


@admin.register(models.Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ['get_phone', 'national_code', 'first_name', 'last_name', 'email', 'gender', 'insurance', 'is_foreign_national', 'city', 'num_of_reserves', 'num_of_comments']
    list_per_page = 15
    list_select_related = ['insurance', 'city', 'user']
    search_fields = ['first_name', 'last_name', 'user__phone']
    autocomplete_fields = ['user', 'insurance', 'province', 'city']
    ordering = ['-created_datetime']

    def get_queryset(self, request):
        return super().get_queryset(request)\
               .annotate(reserves_count=Count('reserves', distinct=True), comments_count=Count('comments', distinct=True))

    @admin.display(description=_('phone'))
    def get_phone(self, patient):
        return patient.user.phone
    
    @admin.display(description=_('# reserves'), ordering='reserves_count')
    def num_of_reserves(self, patient):
        url = (
            reverse('admin:online_reservation_reserve_changelist')
            + '?'
            + urlencode({
                'patient': patient.id
            })
        )

        return format_html('<a href={}>{}</a>', url, patient.reserves_count)
    
    @admin.display(description=_('# comments'), ordering='comments_count')
    def num_of_comments(self, patient):
        url = (
            reverse('admin:online_reservation_comment_changelist')
            + '?'
            + urlencode({
                'patient': patient.id
            })
        )

        return format_html('<a href={}>{}</a>', url, patient.comments_count)


@admin.register(models.Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ['get_phone', 'email', 'first_name', 'last_name', 'medical_council_number', 'gender', 'status', 'city', 
                    'num_of_specialties', 'num_of_reserves', 'num_of_comments']
    list_per_page = 15
    list_select_related = ['city', 'user']
    search_fields = ['first_name', 'last_name']
    autocomplete_fields = ['user', 'province', 'city']
    inlines = [DoctorSpecialtyInline]
    ordering = ['-confirm_datetime']

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)

        status_field = form.base_fields.get('status')
        if (obj is None) or (obj and obj.reserves.count() > 0):
            status_field.choices = [(key, value) for key, value in status_field.choices if key != 'r']
        return form

    def get_queryset(self, request):
        return super().get_queryset(request)\
               .annotate(specialties_count=Count('specialties', distinct=True), reserves_count=Count('reserves', distinct=True), comments_count=Count('comments', distinct=True))

    @admin.display(description=_('phone'))
    def get_phone(self, patient):
        return patient.user.phone
    
    @admin.display(description=_('# specialties'), ordering='specialties_count')
    def num_of_specialties(self, doctor):
        url = (
            reverse('admin:online_reservation_doctorspecialty_changelist')
            + '?'
            + urlencode({
                'doctor': doctor.id
            })
        )

        return format_html('<a href={}>{}</a>', url, doctor.specialties_count)

    @admin.display(description=_('# reserves'), ordering='reserves_count')
    def num_of_reserves(self, doctor):
        url = (
            reverse('admin:online_reservation_reserve_changelist')
            + '?'
            + urlencode({
                'doctor': doctor.id
            })
        )

        return format_html('<a href={}>{}</a>', url, doctor.reserves_count)
    
    @admin.display(description=_('# comments'), ordering='comments_count')
    def num_of_comments(self, doctor):
        url = (
            reverse('admin:online_reservation_comment_changelist')
            + '?'
            + urlencode({
                'doctor': doctor.id
            })
        )

        return format_html('<a href={}>{}</a>', url, doctor.comments_count)


@admin.register(models.Specialty)
class SpecialtyAdmin(admin.ModelAdmin):
    list_display = ['name', 'num_of_doctors']
    list_per_page = 15
    search_fields = ['name']

    def get_queryset(self, request):
        return super().get_queryset(request)\
               .annotate(doctors_count=Count('doctors'))

    @admin.display(description=_('# doctors'), ordering='doctors_count')
    def num_of_doctors(self, specialty):
        url = (
            reverse('admin:online_reservation_doctorspecialty_changelist')
            + '?'
            + urlencode({
                'specialty': specialty.id
            })
        )

        return format_html('<a href={}>{}</a>', url, specialty.doctors_count)


@admin.register(models.DoctorInsurance)
class DoctorInsuranceAdmin(admin.ModelAdmin):
    list_display = ['get_full_name', 'insurance']
    list_per_page = 15
    search_fields = ['doctor__first_name', 'doctor__last_name', 'insurance__name']
    autocomplete_fields = ['doctor', 'insurance']
    list_select_related = ['doctor', 'insurance']

    @admin.display(description=_('full_name'))
    def get_full_name(self, doctor_specialty):
        return doctor_specialty.doctor.full_name


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
    list_display = ['patient', 'get_doctor', 'status', 'rating', 'is_suggest', 'is_anonymous', 'get_created_datetime']
    list_per_page = 15
    list_select_related = ['patient', 'doctor']
    autocomplete_fields = ['patient', 'doctor']
    ordering = ['-created_datetime']
    list_editable = ['status']

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)

        if obj is None:
            status_field = form.base_fields.get('status')
            if status_field:
                status_field.choices = [(key, value) for key, value in status_field.choices if key != 'na']
        return form

    @admin.display(description=_('doctor'))
    def get_doctor(self, comment):
        return comment.doctor.full_name
    
    @admin.display(description=_('created_datetime'), ordering='created_datetime')
    def get_created_datetime(self, comment):
        tehran_time = comment.created_datetime.astimezone(TEHRAN_TZ)
        return tehran_time.strftime('%Y-%m-%d %H:%M:%S')


@admin.register(models.Reserve)
class ReserveAdmin(admin.ModelAdmin):
    list_display = ['patient', 'get_doctor', 'status', 'price', 'get_reserve_datetime', 'celery_task_id', 'celery_payment_expiration_datetime', 'is_expired']
    list_per_page = 15
    list_select_related = ['patient', 'doctor']
    autocomplete_fields = ['patient', 'doctor']
    ordering = ['-reserve_datetime']

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields + ('reserve_datetime', )
        return self.readonly_fields

    @admin.display(description=_('doctor'), ordering='doctor__id')
    def get_doctor(self, reserve):
        return reserve.doctor.full_name
    
    @admin.display(description=_('reserve_datetime'), ordering='reserve_datetime')
    def get_reserve_datetime(self, reserve):
        tehran_time = reserve.reserve_datetime.astimezone(TEHRAN_TZ)
        return tehran_time.strftime('%Y-%m-%d %H:%M:%S')
    
    @admin.display(description=_('is_expired'))
    def is_expired(self, reserve):
        return True if reserve.reserve_datetime < datetime.now(tz=TEHRAN_TZ) + timedelta(minutes=5) else False
