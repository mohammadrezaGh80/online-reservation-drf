from django.contrib import admin

from . import models


@admin.register(models.Province)
class ProvinceAdmin(admin.ModelAdmin):
    pass


@admin.register(models.City)
class CityAdmin(admin.ModelAdmin):
    pass


@admin.register(models.Insurance)
class InsuranceAdmin(admin.ModelAdmin):
    pass


@admin.register(models.Patient)
class PatientAdmin(admin.ModelAdmin):
    pass


@admin.register(models.Doctor)
class DoctorAdmin(admin.ModelAdmin):
    pass


@admin.register(models.Specialty)
class SpecialtyAdmin(admin.ModelAdmin):
    pass


@admin.register(models.DoctorSpecialty)
class DoctorSpecialtyAdmin(admin.ModelAdmin):
    pass


@admin.register(models.Comment)
class CommentAdmin(admin.ModelAdmin):
    pass


@admin.register(models.Reserve)
class ReserveAdmin(admin.ModelAdmin):
    pass
