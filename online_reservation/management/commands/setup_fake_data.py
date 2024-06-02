from django.core.management import BaseCommand

from faker import Faker
import requests
import random
from datetime import datetime, timezone

from online_reservation.models import Province, City, Insurance, Patient, Doctor, \
                                      Specialty, DoctorSpecialty, Comment, Reserve
from online_reservation.factories import (
    InsuranceFactory,
    PatientFactory,
    DoctorFactory,
    SpecialtyFactory,
    CommentFactory,
    ReserveFactory
)

API_LIST_PROVINCES = 'https://iran-locations-api.ir/api/v1/fa/states'
API_LIST_CITIES = 'https://iran-locations-api.ir/api/v1/fa/cities'

fake = Faker(locale='fa_IR')

list_of_models = [Province, City, Insurance, Patient, Doctor, Specialty, 
                  DoctorSpecialty, Comment, Reserve]

NUM_INSURANCES = 20
NUM_PATIENTS = 40
NUM_DOCTORS = 15
NUM_SPECIALTY = 30


class Command(BaseCommand):
    help = 'Generate fake data'

    def handle(self, *args, **kwargs):
        self.stdout.write('Deleting old data...')

        for model in list_of_models:
            model.objects.all().delete()
        
        self.stdout.write('Creating new data...\n')

        # insurances data
        print(f'Adding {NUM_INSURANCES} insurances...', end='')
        all_insurances = [InsuranceFactory() for _ in range(NUM_INSURANCES)]
        print('DONE')

        # provinces & cities data
        print(f'Adding provinces & cities...', end='')
        response = requests.get(API_LIST_PROVINCES)
        list_provinces = response.json()
        
        all_provinces = []
        all_cities = []
        all_provinces_with_cities_dict = {province.get('name'): [] for province in list_provinces}

        for province_dict in list_provinces:
            province = Province(
                name=province_dict.get('name')
            )
            all_provinces.append(province)
            
            response = requests.get(API_LIST_CITIES + f"?state_id={province_dict.get('id')}")
            list_cities = response.json()
            
            for city_dict in list_cities:
                city = City(
                    name=city_dict.get('name'),
                    province=province
                )
                all_cities.append(city)
                all_provinces_with_cities_dict[province.name].append(city)
        
        Province.objects.bulk_create(all_provinces)
        City.objects.bulk_create(all_cities)
        print('DONE')

        # patients data
        print(f'Adding {NUM_PATIENTS} patients...', end='')
        all_patients = []

        for _ in range(NUM_PATIENTS):
            patient = PatientFactory(
                province_id=random.choice(all_provinces).id,
                insurance_id=random.choice(all_insurances).id
            )
            
            patient.city = random.choice(
                all_provinces_with_cities_dict[patient.province.name]
            )
            patient.created_datetime = datetime(year=random.randint(2018, 2019), month=random.randint(1,12),day=random.randint(1,28), tzinfo=timezone.utc)
            patient.save()

            all_patients.append(patient)

        print('DONE')

        # doctors data
        print(f'Adding {NUM_DOCTORS} doctors...', end='')
        all_doctors = []

        for _ in range(NUM_DOCTORS):
            doctor = DoctorFactory(
                province_id=random.choice(all_provinces).id
            )

            doctor.city = random.choice(
                all_provinces_with_cities_dict[doctor.province.name]
            )
            doctor.confirm_datetime = datetime(year=random.randint(2020, 2021), month=random.randint(1,12),day=random.randint(1,28), tzinfo=timezone.utc)
            doctor.save()

            patient = PatientFactory(
                user=doctor.user,
                first_name=doctor.first_name,
                last_name=doctor.last_name,
                birth_date=doctor.birth_date,
                national_code=doctor.national_code,
                email=doctor.email,
                gender=doctor.gender,
                province=doctor.province,
                city=doctor.city,
                insurance_id=random.choice(all_insurances).id
            )
            patient.created_datetime = datetime(year=random.randint(2018, 2019), month=random.randint(1,12),day=random.randint(1,28), tzinfo=timezone.utc)
            patient.save()

            all_doctors.append(doctor)
            all_patients.append(patient)
        
        print('DONE')

        # specialties data
        print(f'Adding {NUM_SPECIALTY} specialties...', end='')
        all_specialties = [SpecialtyFactory() for _ in range(NUM_SPECIALTY)]
        print('DONE')

        # doctor specialties data
        print('Adding doctor specialties...', end='')
        all_doctor_specialties = []

        for doctor in all_doctors:
            specialties = random.sample(all_specialties, k=random.randint(1, 3))
            for specialty in specialties:
                doctor_specialty = DoctorSpecialty.objects.create(
                    doctor_id=doctor.id,
                    specialty_id=specialty.id
                )

                all_doctor_specialties.append(doctor_specialty)
        
        print('DONE')

        # reserves data
        print(f'Adding reserves...', end='')
        all_reserves = []

        for doctor in all_doctors:
            num_of_reserves = random.randint(5, 10)
            for _ in range(num_of_reserves):
                reserve = ReserveFactory(
                    doctor_id=doctor.id
                )
                
                if reserve.status == Reserve.RESERVE_STATUS_PAID:
                    reserve.patient = random.choice(all_patients)
                    reserve.save()

                all_reserves.append(reserve)
        
        print('DONE')

        # comments data
        print(f'Adding comments...', end='')
        all_comments = []

        for patient in all_patients:
            doctors = random.sample(all_doctors, k=random.randint(0, 4))
            for doctor in doctors:
                comment = CommentFactory(
                    patient_id=patient.id,
                    doctor_id=doctor.id
                )
                comment.created_datetime = datetime(year=random.randint(2022, 2024), month=random.randint(1,12),day=random.randint(1,28), tzinfo=timezone.utc)
                comment.save()

                all_comments.append(comment)

        print('DONE')
