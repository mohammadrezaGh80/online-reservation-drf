# Generated by Django 5.0.6 on 2024-06-14 06:52

import online_reservation.validators
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('online_reservation', '0002_alter_doctor_gender_alter_patient_case_history_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name='doctor',
            name='email',
            field=models.EmailField(blank=True, max_length=254, null=True, verbose_name='Email'),
        ),
        migrations.AlterField(
            model_name='doctor',
            name='national_code',
            field=models.CharField(blank=True, max_length=10, validators=[online_reservation.validators.NationalCodeValidator()], verbose_name='National code'),
        ),
        migrations.AlterField(
            model_name='patient',
            name='email',
            field=models.EmailField(blank=True, max_length=254, null=True, verbose_name='Email'),
        ),
        migrations.AlterField(
            model_name='patient',
            name='national_code',
            field=models.CharField(blank=True, max_length=10, validators=[online_reservation.validators.NationalCodeValidator()], verbose_name='National code'),
        ),
        migrations.AddConstraint(
            model_name='doctor',
            constraint=models.UniqueConstraint(condition=models.Q(('national_code', ''), _negated=True), fields=('national_code',), name='doctor_unique_national_code', violation_error_message='This national code has already been registered for a doctor'),
        ),
        migrations.AddConstraint(
            model_name='doctor',
            constraint=models.UniqueConstraint(condition=models.Q(('email', ''), _negated=True), fields=('email',), name='doctor_unique_email', violation_error_message='This email has already been registered for a doctor'),
        ),
        migrations.AddConstraint(
            model_name='patient',
            constraint=models.UniqueConstraint(condition=models.Q(('national_code', ''), _negated=True), fields=('national_code',), name='patient_unique_national_code', violation_error_message='This national code has already been registered for a patient'),
        ),
        migrations.AddConstraint(
            model_name='patient',
            constraint=models.UniqueConstraint(condition=models.Q(('email', ''), _negated=True), fields=('email',), name='patient_unique_email', violation_error_message='This email has already been registered for a patient'),
        ),
    ]
