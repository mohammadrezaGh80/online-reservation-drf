from django.utils.translation import gettext_lazy as _
from django.shortcuts import get_object_or_404
from django.db.models import Subquery, OuterRef
from rest_framework.exceptions import ValidationError

import django_filters
from datetime import date, timedelta, datetime, timezone

from .models import Doctor, Patient, Province, City, Insurance, Specialty, Reserve


TEHRAN_TZ = timezone(timedelta(hours=3, minutes=30))


class PersonFilter(django_filters.FilterSet):
    PERSON_GENDER_MALE = 'm'
    PERSON_GENDER_FEMALE = 'f'
    PERSON_GENDER_NOT_DEFINED = 'n'

    PERSON_GENDER = [
        (PERSON_GENDER_MALE, _('Male')),
        (PERSON_GENDER_FEMALE, _('Female')),
        (PERSON_GENDER_NOT_DEFINED, _('Not defined'))
    ]

    gender = django_filters.ChoiceFilter(field_name='gender', choices=PERSON_GENDER, method='filter_gender', label='gender')
    age = django_filters.NumberFilter(field_name='birth_date', method='filter_age', label='age')
    age_max = django_filters.NumberFilter(field_name='birth_date', method='filter_age_max', label='age_max')
    age_min = django_filters.NumberFilter(field_name='birth_date', method='filter_age_min', label='age_min')
    province = django_filters.NumberFilter(field_name='province', method='filter_province', label='province')
    city = django_filters.NumberFilter(field_name='city', method='filter_city', label='city')

    def filter_gender(self, queryset, field_name, value):
        if value == self.PERSON_GENDER_MALE:
            filter_condition = {field_name: self.PERSON_GENDER_MALE}
            return queryset.filter(**filter_condition)
        elif value == self.PERSON_GENDER_FEMALE:
            filter_condition = {field_name: self.PERSON_GENDER_FEMALE}
            return queryset.filter(**filter_condition)
        elif value == self.PERSON_GENDER_NOT_DEFINED:
            filter_condition = {field_name: ''}
            return queryset.filter(**filter_condition)
    
    def filter_age(self, queryset, field_name, value):
        max_birth_date = date.today() - timedelta(days=int(value * 365))
        min_birth_date = date.today() - timedelta(days=int((value + 1) * 365))
        filter_condition = {f'{field_name}__range': (min_birth_date, max_birth_date)}
        return queryset.filter(**filter_condition).order_by('-id')
    
    def filter_age_min(self, queryset, field_name, value):
        max_birth_date = date.today() - timedelta(days=int(value * 365))
        filter_condition = {f'{field_name}__lte': max_birth_date}
        return queryset.filter(**filter_condition).order_by('-birth_date')
    
    def filter_age_max(self, queryset, field_name, value):
        min_birth_date = date.today() - timedelta(days=int((value + 1) * 365))
        filter_condition = {f'{field_name}__gte': min_birth_date}
        return queryset.filter(**filter_condition).order_by('birth_date')
    
    def filter_province(self, queryset, field_name, value):
        province = get_object_or_404(Province, pk=value)
        filter_condition = {field_name: province}
        return queryset.filter(**filter_condition)
    
    def filter_city(self, queryset, field_name, value):
        city = get_object_or_404(City, pk=value)
        filter_condition = {field_name: city}
        return queryset.filter(**filter_condition)


class PatientFilter(PersonFilter):
    is_foreign_national = django_filters.BooleanFilter(field_name='is_foreign_national', label='is_foreign_national')
    insurance = django_filters.NumberFilter(field_name='insurance', method='filter_insurance', label='insurance')
    
    def filter_insurance(self, queryset, field_name, value):
        insurance = get_object_or_404(Insurance, pk=value)
        filter_condition = {field_name: insurance}
        return queryset.filter(**filter_condition)


class DoctorFilter(PersonFilter):
    specialty = django_filters.NumberFilter(field_name='specialties__specialty', method='filter_specialty', label='specialty')
    insurance = django_filters.NumberFilter(field_name='insurances__insurance', method='filter_insurance', label='insurance')
    has_free_reserve = django_filters.BooleanFilter(field_name='reserves__reserve_datetime', method='filter_has_free_reserve', label='has_free_reserve')

    def filter_specialty(self, queryset, field_name, value):
        specialty = get_object_or_404(Specialty, pk=value)
        filter_condition = {field_name: specialty}
        return queryset.filter(**filter_condition)
    
    def filter_insurance(self, queryset, field_name, value):
        insurance = get_object_or_404(Insurance, pk=value)
        filter_condition = {field_name: insurance}
        return queryset.filter(**filter_condition)
    
    def filter_has_free_reserve(self, queryset, field_name, value):
        if value:
            first_free_reserve_subquery = Reserve.objects.filter(
                doctor=OuterRef('pk'),
                reserve_datetime__gte=datetime.now(tz=TEHRAN_TZ),
                patient__isnull=True
            ).order_by('reserve_datetime').values('reserve_datetime')[:1]

            return queryset.annotate(
                first_free_reserve_datetime=Subquery(first_free_reserve_subquery)
            ).filter(
                first_free_reserve_datetime__isnull=False
            ).order_by('first_free_reserve_datetime')

        return queryset


class CommentListWaitingFilter(django_filters.FilterSet):
    patient = django_filters.NumberFilter(field_name='patient', method='filter_patient', label='patient')
    doctor = django_filters.NumberFilter(field_name='doctor', method='filter_doctor', label='doctor')

    def filter_patient(self, queryset, field_name, value):
        patient = get_object_or_404(Patient, pk=value)
        filter_condition = {field_name: patient}
        return queryset.filter(**filter_condition)

    def filter_doctor(self, queryset, field_name, value):
        doctor = get_object_or_404(Doctor, pk=value)
        filter_condition = {field_name: doctor}
        return queryset.filter(**filter_condition)


class ReserveDoctorFilter(django_filters.FilterSet):
    is_expired = django_filters.BooleanFilter(field_name='reserve_datetime', method='filter_is_expired', label='is_expired')
    year = django_filters.NumberFilter(field_name='reserve_datetime', lookup_expr='year', label='year')
    month = django_filters.NumberFilter(field_name='reserve_datetime', lookup_expr='month', label='month')
    day = django_filters.NumberFilter(field_name='reserve_datetime', lookup_expr='day', label='day')

    def filter_is_expired(self, queryset, field_name, value):
        if value:
            filter_condition = {f'{field_name}__lt': datetime.now()}
        else:
            filter_condition = {f'{field_name}__gte': datetime.now()}
        return queryset.filter(**filter_condition)

    class Meta:
        model = Reserve
        fields = ['status', 'is_expired', 'year', 'month', 'day']


class AppointmentDoctorFilter(django_filters.FilterSet):
    reserve_date = django_filters.DateFilter(field_name='reserve_datetime__date', method='filter_reserve_date', label='reserve_date') 

    def filter_reserve_date(self, queryset, field_name, value):
        if value < date.today():
            raise ValidationError({'reserve_date': _('Cannot select a date before today.')})
        filter_condition = {field_name: value}
        return queryset.filter(**filter_condition)

    class Meta:
        model = Reserve
        fields = ['reserve_date']
