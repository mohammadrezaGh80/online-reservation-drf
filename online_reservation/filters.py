from django.utils.translation import gettext_lazy as _
from django.shortcuts import get_object_or_404

import django_filters
from datetime import date, timedelta

from .models import Province, City, Insurance


class PatientFilter(django_filters.FilterSet):

    PATIENT_GENDER_MALE = 'm'
    PATIENT_GENDER_FEMALE = 'f'
    PATIENT_GENDER_NOT_DEFINED = 'n'

    PATIENT_GENDER = [
        (PATIENT_GENDER_MALE, _('Male')),
        (PATIENT_GENDER_FEMALE, _('Female')),
        (PATIENT_GENDER_NOT_DEFINED, _('Not defined'))
    ]

    gender = django_filters.ChoiceFilter(field_name='gender', choices=PATIENT_GENDER, method='filter_gender', label='gender')
    age = django_filters.NumberFilter(field_name='birth_date', method='filter_age', label='age')
    age_max = django_filters.NumberFilter(field_name='birth_date', method='filter_age_max', label='age_max')
    age_min = django_filters.NumberFilter(field_name='birth_date', method='filter_age_min', label='age_min')
    is_foreign_national = django_filters.BooleanFilter(field_name='is_foreign_national', label='is_foreign_national')
    province = django_filters.NumberFilter(field_name='province', method='filter_province', label='province')
    city = django_filters.NumberFilter(field_name='city', method='filter_city', label='city')
    insurance = django_filters.NumberFilter(field_name='insurance', method='filter_insurance', label='insurance')

    def filter_gender(self, queryset, field_name, value):
        if value == self.PATIENT_GENDER_MALE:
            filter_condition = {field_name: self.PATIENT_GENDER_MALE}
            return queryset.filter(**filter_condition)
        elif value == self.PATIENT_GENDER_FEMALE:
            filter_condition = {field_name: self.PATIENT_GENDER_FEMALE}
            return queryset.filter(**filter_condition)
        elif value == self.PATIENT_GENDER_NOT_DEFINED:
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
        province = get_object_or_404(City, pk=value)
        filter_condition = {field_name: province}
        return queryset.filter(**filter_condition)
    
    def filter_insurance(self, queryset, field_name, value):
        province = get_object_or_404(Insurance, pk=value)
        filter_condition = {field_name: province}
        return queryset.filter(**filter_condition)
