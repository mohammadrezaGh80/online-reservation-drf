from django.contrib.auth import get_user_model
from django.db.models import signals

from factory.django import DjangoModelFactory

import random
import factory
from datetime import datetime, timezone
from faker import Faker

from . import models

User = get_user_model()
fake = Faker(locale='fa_IR')


class InsuranceFactory(DjangoModelFactory):
    class Meta:
        model = models.Insurance
    
    name = factory.LazyFunction(lambda: fake.word())


@factory.django.mute_signals(signals.post_save)
class CustomUserFactory(DjangoModelFactory):
    class Meta:
        model = User

    phone = factory.Sequence(lambda n: "09%09d" % n)
    password = factory.PostGenerationMethodCall('set_unusable_password')

    @classmethod
    def _setup_next_sequence(cls):
        try:
            user = User.objects.latest("phone")
            return int(user.phone[2:]) + 1
        except User.DoesNotExist:
            return 1


class PatientFactory(DjangoModelFactory):
    class Meta:
        model = models.Patient
    
    user = factory.SubFactory(CustomUserFactory)
    first_name = factory.LazyFunction(lambda: fake.first_name())
    last_name = factory.LazyFunction(lambda: fake.last_name())
    birth_date = factory.LazyFunction(lambda: fake.date_time_ad(start_datetime=datetime(1980, 1, 1), end_datetime=datetime(2014, 1, 1)))
    national_code = factory.Sequence(lambda n: "1%09d" % n)
    email = factory.Sequence(lambda n: "%s%d@gmail.com" %(fake.language_name().replace('-', '').replace(' ', ''), n))
    gender = factory.LazyFunction(lambda: random.choice(models.Person.PERSON_GENDER)[0])
    case_history = factory.LazyFunction(lambda: fake.sentence(nb_words=10, variable_nb_words=True))


    @classmethod
    def _setup_next_sequence(cls):
        try:
            patient = models.Patient.objects.latest("id")
            return int(patient.national_code[1:]) + 1
        except models.Patient.DoesNotExist:
            return 1
        

class DoctorFactory(DjangoModelFactory):
    class Meta:
        model = models.Doctor

    user = factory.SubFactory(CustomUserFactory)
    first_name = factory.LazyFunction(lambda: fake.first_name())
    last_name = factory.LazyFunction(lambda: fake.last_name())
    birth_date = factory.LazyFunction(lambda: fake.date_time_ad(start_datetime=datetime(1980, 1, 1), end_datetime=datetime(2014, 1, 1)))
    national_code = factory.Sequence(lambda n: "1%09d" % n)
    email = factory.Sequence(lambda n: "%s%d@gmail.com" %(fake.language_name(), n))
    gender = factory.LazyFunction(lambda: random.choice([models.Person.PERSON_GENDER_MALE, models.Person.PERSON_GENDER_FEMALE])) 
    medical_council_number = factory.Sequence(lambda n: "1%04d" % n)
    status = factory.LazyFunction(lambda:  models.Doctor.DOCTOR_STATUS_ACCEPTED)
    bio = factory.LazyFunction(lambda: fake.sentence(nb_words=10, variable_nb_words=True))
    office_address = factory.LazyFunction(lambda: fake.sentence(nb_words=10, variable_nb_words=True))

    @classmethod
    def _setup_next_sequence(cls):
        try:
            doctor = models.Doctor.objects.latest("id")
            return int(doctor.national_code[1:]) + 1
        except models.Doctor.DoesNotExist:
            patient = models.Patient.objects.latest("id")
            return int(patient.national_code[1:]) + 1
        

class SpecialtyFactory(DjangoModelFactory):
    class Meta:
        model = models.Specialty
    
    name = factory.LazyFunction(lambda: fake.word())


class CommentFactory(DjangoModelFactory):
    class Meta:
        model = models.Comment
    
    rating = factory.LazyFunction(lambda: random.choice(models.Comment.COMMENT_RATING)[0])
    is_suggest = factory.LazyFunction(lambda: fake.boolean())
    waiting_time = factory.LazyFunction(lambda: random.choice(models.Comment.COMMENT_WAITING_TIME)[0])
    is_anonymous = factory.LazyFunction(lambda: fake.boolean())
    body = factory.LazyFunction(lambda: fake.sentence(nb_words=12, variable_nb_words=True))


def generate_reserve_datetime():
    dt = fake.unique.date_time_ad(start_datetime=datetime(2022, 1, 1), end_datetime=datetime(2024, 1, 1), tzinfo=timezone.utc)
    return dt.replace(second=0, microsecond=0)


class ReserveFactory(DjangoModelFactory):
    class Meta:
        model = models.Reserve
    
    status = factory.LazyFunction(lambda: random.choice(models.Reserve.RESERVE_STATUS)[0])
    price = factory.LazyFunction(lambda: round(random.randint(5000, 100000), -3))
    reserve_datetime = factory.LazyFunction(generate_reserve_datetime)
