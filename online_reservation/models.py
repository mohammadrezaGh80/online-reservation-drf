from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.db.models import Q
from django.core.exceptions import ValidationError

from .validators import NationalCodeValidator, MedicalCouncilNumberValidator

User = get_user_model()


class Province(models.Model):
    name = models.CharField(max_length=255, unique=True, verbose_name=_('Name'))

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('Province')
        verbose_name_plural = _('Provinces')


class City(models.Model):
    name = models.CharField(max_length=255, verbose_name=_('Name'))
    province = models.ForeignKey(Province, on_delete=models.CASCADE, related_name='cities', verbose_name=_('Province'))

    def __str__(self):
        return self.name
    
    def clean(self):
        super().clean()

        if City.objects.filter(province=self.province, name=self.name).exclude(id=self.id).exists():
            raise ValidationError(_('There is a city with this name in %(province_name)s.' % {'province_name': self.province.name}))

    class Meta:
        verbose_name = _('City')
        verbose_name_plural = _('Cities')


class Insurance(models.Model):
    name = models.CharField(max_length=255, verbose_name=_('Name'))

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('Insurance')
        verbose_name_plural = _('Insurances')


class Person(models.Model):
    national_code_validator = NationalCodeValidator()

    PERSON_GENDER_MALE = 'm'
    PERSON_GENDER_FEMALE = 'f'
    PERSON_GENDER_NOT_DEFINED = ''

    PERSON_GENDER = [
        (PERSON_GENDER_MALE, _('Male')),
        (PERSON_GENDER_FEMALE, _('Female')),
        (PERSON_GENDER_NOT_DEFINED, _('Not defined'))
    ]

    first_name = models.CharField(max_length=255, blank=True, verbose_name=_('First name'))
    last_name = models.CharField(max_length=255, blank=True, verbose_name=_('Last name'))
    birth_date = models.DateField(blank=True, null=True, verbose_name=_('Birth date'))
    national_code = models.CharField(max_length=10, blank=True, validators=[national_code_validator], verbose_name=_('National code'))
    email = models.EmailField(blank=True, verbose_name=_('Email'))
    gender = models.CharField(max_length=1, choices=PERSON_GENDER, blank=True, default=PERSON_GENDER_NOT_DEFINED, verbose_name=_('Gender'))

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    class Meta:
        abstract = True


class Patient(Person):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='patient', verbose_name=_('User'))
    insurance = models.ForeignKey(Insurance, blank=True, null=True, on_delete=models.PROTECT, related_name='patients', verbose_name=_('Insurance'))
    case_history = models.TextField(blank=True, verbose_name=_('Case history'))
    is_foreign_national = models.BooleanField(default=False, verbose_name=_('Is foreign national'))
    province = models.ForeignKey(Province, blank=True, null=True, on_delete=models.PROTECT, related_name='patients', verbose_name=_('Province'))
    city = models.ForeignKey(City, blank=True, null=True, on_delete=models.PROTECT, related_name='patients', verbose_name=_('City')) # TODO: validate for city that exist in province

    created_datetime = models.DateTimeField(auto_now_add=True, verbose_name=_('Created datetime'))

    def clean(self):
        super().clean()

        if not self.national_code and not self.is_foreign_national:
            raise ValidationError(_('national_code field may not be blank.'))
        
        if self.province and not self.city:
            raise ValidationError(_('city field is required.'))
        elif not self.province and self.city:
            raise ValidationError(_('province field is required.'))
        elif self.city and self.province and not City.objects.filter(id=self.city.id, province_id=self.province.id).exists():
            raise ValidationError(_("There isn't %(city_name)s city in %(province_name)s province.") % {'city_name': self.city.name, 'province_name': self.province.name})

    def save(self, *args, **kwargs):
        if self.is_foreign_national:
            self.national_code = ''
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.full_name if self.full_name else self.user.phone

    class Meta:
        verbose_name = _('Patient')
        verbose_name_plural = _('Patients')
        constraints = [
            models.UniqueConstraint(
                fields=['national_code'],
                name='patient_unique_national_code',
                condition=~Q(national_code=''),
                violation_error_message=_('This national code has already been registered for a patient')
            ),
            models.UniqueConstraint(
                fields=['email'],
                name='patient_unique_email',
                condition=~Q(email=''),
                violation_error_message=_('This email has already been registered for a patient')
            )
        ]
    

class Doctor(Person):
    medical_council_number_validator = MedicalCouncilNumberValidator()

    DOCTOR_STATUS_WAITING = 'w'
    DOCTOR_STATUS_ACCEPTED = 'a'
    DOCTOR_STATUS_REJECTED = 'r'

    DOCTOR_STATUS = [
        (DOCTOR_STATUS_WAITING, _('Waiting')),
        (DOCTOR_STATUS_ACCEPTED, _('Accepted')),
        (DOCTOR_STATUS_REJECTED, _('Rejected'))
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='doctor', verbose_name=_('User'))
    medical_council_number = models.CharField(max_length=5, unique=True, validators=[medical_council_number_validator], verbose_name=_('medical council number'))
    status = models.CharField(max_length=1, choices=DOCTOR_STATUS, default=DOCTOR_STATUS_WAITING, verbose_name=_('Status'))
    bio = models.TextField(blank=True, verbose_name=_('Bio'))
    office_address = models.TextField(blank=True, verbose_name=_('Office address')) # TODO: when doctor register a reservation should have office address
    province = models.ForeignKey(Province, blank=True, null=True, on_delete=models.PROTECT, related_name='doctors', verbose_name=_('Province'))
    city = models.ForeignKey(City, blank=True, null=True, on_delete=models.PROTECT, related_name='doctors', verbose_name=_('City')) # TODO: validate for city that exist in province

    confirm_datetime = models.DateTimeField(blank=True, null=True, verbose_name=_('Confirm datetime')) # TODO: when status is accepted, this field be filled

    def clean(self):
        super().clean()

        if self.province and not self.city:
            raise ValidationError(_('city field is required.'))
        elif not self.province and self.city:
            raise ValidationError(_('province field is required.'))
        elif self.city and self.province and not City.objects.filter(id=self.city.id, province_id=self.province.id).exists():
            raise ValidationError(_("There isn't %(city_name)s city in %(province_name)s province.") % {'city_name': self.city.name, 'province_name': self.province.name})

    def __str__(self):
        return f'{self.full_name}(M.C.NO: {self.medical_council_number})'
    
    class Meta:
        verbose_name = _('Doctor')
        verbose_name_plural = _('Doctors')
        constraints = [
            models.UniqueConstraint(
                fields=['national_code'],
                name='doctor_unique_national_code',
                condition=~Q(national_code=''),
                violation_error_message=_('This national code has already been registered for a doctor')
            ),
            models.UniqueConstraint(
                fields=['email'],
                name='doctor_unique_email',
                condition=~Q(email=''),
                violation_error_message=_('This email has already been registered for a doctor')
            )
        ]


class DoctorInsurance(models.Model):
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='insurances', verbose_name=_('Doctor'))
    insurance = models.ForeignKey(Insurance, on_delete=models.CASCADE, related_name='doctors', verbose_name=_('Insurance'))

    def __str__(self):
        return f'{self.doctor.full_name} covers {self.insurance.name} insurance'
    
    class Meta:
        unique_together = [['doctor', 'insurance']]
        verbose_name = _('Doctor insurance')
        verbose_name_plural = _('Doctor insurances')


class Specialty(models.Model):
    name = models.CharField(max_length=255, unique=True, verbose_name=_('Name'))

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = _('Specialty')
        verbose_name_plural = _('Specialties')


class DoctorSpecialty(models.Model):
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='specialties', verbose_name=_('Doctor'))
    specialty = models.ForeignKey(Specialty, on_delete=models.CASCADE, related_name='doctors', verbose_name=_('Specialty'))

    def __str__(self):
        return f'{self.doctor.full_name} specialist {self.specialty}'
    
    class Meta:
        unique_together = [['doctor', 'specialty']]
        verbose_name = _('Doctor specialty')
        verbose_name_plural = _('Doctor specialties')


class Comment(models.Model):
    COMMENT_RATING_VERY_BAD = 1
    COMMENT_RATING_BAD = 2
    COMMENT_RATING_NORMAL = 3
    COMMENT_RATING_GOOD = 4
    COMMENT_RATING_EXCELLENT = 5

    COMMENT_RATING = [
        (COMMENT_RATING_VERY_BAD, _('Very bad')),
        (COMMENT_RATING_BAD, _('Bad')),
        (COMMENT_RATING_NORMAL, _('Normal')),
        (COMMENT_RATING_GOOD, _('Good')),
        (COMMENT_RATING_EXCELLENT, _('Excellent'))
    ]

    COMMENT_WAITING_TIME_0_TO_15_MINUTES = 0
    COMMENT_WAITING_TIME_15_TO_45_MINUTES = 1
    COMMENT_WAITING_TIME_45_TO_90_MINUTES = 2
    COMMENT_WAITING_TIME_MORE_THAN_90_MINUTES = 3

    COMMENT_WAITING_TIME = [
        (COMMENT_WAITING_TIME_0_TO_15_MINUTES, _('0 to 15 minutes')),
        (COMMENT_WAITING_TIME_15_TO_45_MINUTES, _('15 to 45 minutes')),
        (COMMENT_WAITING_TIME_45_TO_90_MINUTES, _('45 to 90 minutes')),
        (COMMENT_WAITING_TIME_MORE_THAN_90_MINUTES, _('More than 90 minutes'))
    ]

    COMMENT_STATUS_WAITING = 'w'
    COMMENT_STATUS_APPROVED = 'a'
    COMMENT_STATUS_NOT_APPROVED = 'na'

    COMMENT_STATUS = [
        (COMMENT_STATUS_WAITING, _('Waiting')),
        (COMMENT_STATUS_APPROVED, _('Approved')),
        (COMMENT_STATUS_NOT_APPROVED, _('Not approved'))
    ]

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='comments', verbose_name=_('Patient'))
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='comments', verbose_name=_('Doctor'))
    rating = models.IntegerField(choices=COMMENT_RATING, verbose_name=_('Rating'))
    is_suggest = models.BooleanField(verbose_name=_('Is suggest'))
    waiting_time = models.IntegerField(choices=COMMENT_WAITING_TIME, verbose_name=_('Waiting time'))
    is_anonymous = models.BooleanField(default=False, verbose_name=_('Is anonymous')) # if True, should show Unknown instead of name
    body = models.TextField(verbose_name=_('Body'))
    status = models.CharField(max_length=2, choices=COMMENT_STATUS, default=COMMENT_STATUS_WAITING, verbose_name=_('Status'))

    created_datetime = models.DateTimeField(auto_now_add=True, verbose_name=_('Created datetime'))

    def __str__(self):
        return f'{self.body[:30]}'
    
    class Meta:
        verbose_name = _('Comment')
        verbose_name_plural = _('Comments')


class Reserve(models.Model):
    RESERVE_STATUS_PAID = 'p'
    RESERVE_STATUS_UNPAID = 'u'

    RESERVE_STATUS = [
        (RESERVE_STATUS_PAID, _('Paid')),
        (RESERVE_STATUS_UNPAID, _('Unpaid'))
    ]

    doctor = models.ForeignKey(Doctor, on_delete=models.PROTECT, related_name='reserves', verbose_name=_('Doctor'))
    patient = models.ForeignKey(Patient, blank=True, null=True, on_delete=models.PROTECT, related_name='reserves', verbose_name=_('Patient')) # TODO: patient can cancel reserve for 20 minutes
    status = models.CharField(max_length=1, choices=RESERVE_STATUS, default=RESERVE_STATUS_UNPAID, verbose_name=_('Status')) # TODO: after 20 minutes delete patient's reserve
    price = models.PositiveIntegerField(verbose_name=_('Price'))
    reserve_datetime = models.DateTimeField(verbose_name=_('Reserve datetime')) # TODO: in same day and time, doctor can't add more than one reserve && if reserve_datetime has passed delete it reserve

    zarinpal_authority = models.CharField(max_length=255, blank=True, verbose_name=_('Zarinpal authority'))
    zarinpal_ref_id = models.CharField(max_length=255, blank=True, verbose_name=_('Zarinpal ref_id'))

    celery_task_id = models.CharField(blank=True, max_length=255, verbose_name=_('Celery task_id'))
    celery_payment_expiration_datetime = models.DateTimeField(blank=True, null=True, verbose_name=_('Celery payment expiration datetime'))

    def clean(self):
        super().clean()
        
        if Reserve.objects.filter(doctor=self.doctor, reserve_datetime=self.reserve_datetime.replace(second=0, microsecond=0)).exclude(id=self.id).exists():
            raise ValidationError(
                _("A doctor can't have two or more reserves at the same time(%(reserve_datetime)s)." % {'reserve_datetime': self.reserve_datetime.strftime('%Y-%m-%d %H:%M')})
            )
    
    def save(self, *args, **kwargs):
        self.reserve_datetime = self.reserve_datetime.replace(second=0, microsecond=0)
        return super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.patient}(Doctor: {self.doctor.first_name}): {self.reserve_datetime}' # TODO: if not exist patient, show proper str

    class Meta:
        verbose_name = _('Reserve')
        verbose_name_plural = _('Reserves')
