# Generated by Django 5.0.6 on 2024-06-02 12:45

import django.db.models.deletion
import online_reservation.validators
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='City',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, verbose_name='Name')),
            ],
            options={
                'verbose_name': 'City',
                'verbose_name_plural': 'Cities',
            },
        ),
        migrations.CreateModel(
            name='Insurance',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, verbose_name='Name')),
            ],
            options={
                'verbose_name': 'Insurance',
                'verbose_name_plural': 'Insurances',
            },
        ),
        migrations.CreateModel(
            name='Province',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, verbose_name='Name')),
            ],
            options={
                'verbose_name': 'Province',
                'verbose_name_plural': 'Provinces',
            },
        ),
        migrations.CreateModel(
            name='Specialty',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, verbose_name='Name')),
            ],
            options={
                'verbose_name': 'Specialty',
                'verbose_name_plural': 'Specialties',
            },
        ),
        migrations.CreateModel(
            name='Doctor',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('first_name', models.CharField(blank=True, max_length=255, verbose_name='First name')),
                ('last_name', models.CharField(blank=True, max_length=255, verbose_name='Last name')),
                ('birth_date', models.DateField(blank=True, null=True, verbose_name='Birth date')),
                ('national_code', models.CharField(blank=True, max_length=10, unique=True, validators=[online_reservation.validators.NationalCodeValidator()], verbose_name='National code')),
                ('email', models.EmailField(blank=True, max_length=254, null=True, unique=True, verbose_name='Email')),
                ('gender', models.CharField(choices=[('m', 'Male'), ('f', 'Female'), ('', 'Not defined')], default='', max_length=1, verbose_name='Gender')),
                ('medical_council_number', models.CharField(max_length=5, unique=True, validators=[online_reservation.validators.MedicalCouncilNumberValidator()], verbose_name='medical council number')),
                ('status', models.CharField(choices=[('w', 'Waiting'), ('a', 'Accepted'), ('r', 'Rejected')], default='w', max_length=1, verbose_name='Status')),
                ('bio', models.TextField(blank=True, verbose_name='Bio')),
                ('office_address', models.TextField(blank=True, verbose_name='Office address')),
                ('confirm_datetime', models.DateTimeField(blank=True, null=True, verbose_name='Confirm datetime')),
                ('city', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='doctors', to='online_reservation.city', verbose_name='City')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='doctor', to=settings.AUTH_USER_MODEL, verbose_name='User')),
                ('province', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='doctors', to='online_reservation.province', verbose_name='Province')),
            ],
            options={
                'verbose_name': 'Doctor',
                'verbose_name_plural': 'Doctors',
            },
        ),
        migrations.CreateModel(
            name='Patient',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('first_name', models.CharField(blank=True, max_length=255, verbose_name='First name')),
                ('last_name', models.CharField(blank=True, max_length=255, verbose_name='Last name')),
                ('birth_date', models.DateField(blank=True, null=True, verbose_name='Birth date')),
                ('national_code', models.CharField(blank=True, max_length=10, unique=True, validators=[online_reservation.validators.NationalCodeValidator()], verbose_name='National code')),
                ('email', models.EmailField(blank=True, max_length=254, null=True, unique=True, verbose_name='Email')),
                ('gender', models.CharField(choices=[('m', 'Male'), ('f', 'Female'), ('', 'Not defined')], default='', max_length=1, verbose_name='Gender')),
                ('case_history', models.TextField(verbose_name='Case history')),
                ('is_foreign_national', models.BooleanField(default=False, verbose_name='Is foreign national')),
                ('created_datetime', models.DateTimeField(auto_now_add=True, verbose_name='Created datetime')),
                ('city', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='patients', to='online_reservation.city', verbose_name='City')),
                ('insurance', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='patients', to='online_reservation.insurance', verbose_name='Insurance')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='patient', to=settings.AUTH_USER_MODEL, verbose_name='User')),
                ('province', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='patients', to='online_reservation.province', verbose_name='Province')),
            ],
            options={
                'verbose_name': 'Patient',
                'verbose_name_plural': 'Patients',
            },
        ),
        migrations.CreateModel(
            name='Comment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rating', models.IntegerField(choices=[(1, 'Very bad'), (2, 'Bad'), (3, 'Normal'), (4, 'Good'), (5, 'Excellent')], verbose_name='Rating')),
                ('is_suggest', models.BooleanField(verbose_name='Is suggest')),
                ('waiting_time', models.IntegerField(choices=[(0, '0 to 15 minutes'), (1, '15 to 45 minutes'), (2, '45 to 90 minutes'), (3, 'More than 90 minutes')], verbose_name='Waiting time')),
                ('is_anonymous', models.BooleanField(default=False, verbose_name='Is anonymous')),
                ('body', models.TextField(verbose_name='Body')),
                ('created_datetime', models.DateTimeField(auto_now_add=True, verbose_name='Created datetime')),
                ('doctor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='comments', to='online_reservation.doctor', verbose_name='Doctor')),
                ('patient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='comments', to='online_reservation.patient', verbose_name='Patient')),
            ],
            options={
                'verbose_name': 'Comment',
                'verbose_name_plural': 'Comments',
            },
        ),
        migrations.AddField(
            model_name='city',
            name='province',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='cities', to='online_reservation.province', verbose_name='Province'),
        ),
        migrations.CreateModel(
            name='Reserve',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('p', 'Paid'), ('u', 'Unpaid')], default='u', max_length=1, verbose_name='Status')),
                ('price', models.PositiveIntegerField(verbose_name='Price')),
                ('reserve_datetime', models.DateTimeField(verbose_name='Reserve datetime')),
                ('doctor', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='reserves', to='online_reservation.doctor', verbose_name='Doctor')),
                ('patient', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='reserves', to='online_reservation.patient', verbose_name='Patient')),
            ],
            options={
                'verbose_name': 'Reserve',
                'verbose_name_plural': 'Reserves',
            },
        ),
        migrations.CreateModel(
            name='DoctorSpecialty',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('doctor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='specialties', to='online_reservation.doctor', verbose_name='Doctor')),
                ('specialty', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='doctors', to='online_reservation.specialty', verbose_name='Specialty')),
            ],
            options={
                'verbose_name': 'Doctor specialty',
                'verbose_name_plural': 'Doctor specialties',
            },
        ),
    ]
