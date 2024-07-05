from django.contrib import admin
from django.db.models import Count
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.utils.http import urlencode
from django.utils.html import format_html

from datetime import datetime, timezone

from . import models


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
    list_display = ['name']
    list_per_page = 15
    search_fields = ['name']


@admin.register(models.Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ['get_phone', 'email', 'first_name', 'last_name', 'gender', 'insurance', 'is_foreign_national', 'city', 'num_of_reserves', 'num_of_comments']
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
    list_display = ['get_phone', 'email', 'first_name', 'last_name', 'medical_council_number', 'gender', 'status', 'city', 'num_of_specialties', 'num_of_reserves']
    list_per_page = 15
    list_select_related = ['city', 'user']
    search_fields = ['first_name', 'last_name']
    autocomplete_fields = ['user', 'province', 'city']
    ordering = ['-confirm_datetime']

    def get_queryset(self, request):
        return super().get_queryset(request)\
               .annotate(specialties_count=Count('specialties', distinct=True), reserves_count=Count('reserves', distinct=True))

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
    
    @admin.display(description=_('reserve_datetime'), ordering='reserve_datetime')
    def get_reserve_datetime(self, reserve):
        return reserve.reserve_datetime.strftime('%Y-%m-%d %H:%M:%S')
    
    @admin.display(description=_('is_expired'))
    def is_expired(self, reserve):
        return True if reserve.reserve_datetime < datetime.now(timezone.utc) else False
