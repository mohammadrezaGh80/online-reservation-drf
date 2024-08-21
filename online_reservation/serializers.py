from django.utils.translation import gettext as _
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Prefetch
from rest_framework import serializers
from rest_framework.exceptions import NotFound

from datetime import date, datetime, timezone, timedelta

from .models import Doctor, DoctorSpecialty, Insurance, Patient, Province, City, Reserve, Specialty, DoctorInsurance, Comment
from .validators import NationalCodeValidator


TEHRAN_TZ = timezone(timedelta(hours=3, minutes=30))


class ProvinceSerializer(serializers.ModelSerializer):

    class Meta:
        model = Province
        fields = ['id', 'name']


class ProvinceDetailSerializer(serializers.ModelSerializer):
    cities_count = serializers.SerializerMethodField()

    class Meta:
        model = Province
        fields = ['id', 'name', 'cities_count']

    def get_cities_count(self, province):
        return province.cities.count()


class CitySerializer(serializers.ModelSerializer):

    class Meta:
        model = City
        fields = ['id', 'name']

    def validate_name(self, name):
        province = self.context.get('province')

        try:
            City.objects.get(province=province, name=name)
        except City.DoesNotExist:
            return name
        else:
            raise serializers.ValidationError(_('There is a city with this name in %(province_name)s province.' % {'province_name': province.name}))

    def create(self, validated_data):
        province = self.context.get('province')
        return City.objects.create(province=province, **validated_data)


class InsuranceSerializer(serializers.ModelSerializer):

    class Meta:
        model = Insurance
        fields = ['id', 'name']


class InsuranceDetailSerializer(serializers.ModelSerializer):
    patient_count = serializers.SerializerMethodField()

    class Meta:
        model = Insurance
        fields = ['id', 'name', 'patient_count']

    def get_patient_count(self, insurance):
        return insurance.patients.count()
    

class SpecialtySerializer(serializers.ModelSerializer):

    class Meta:
        model = Specialty
        fields = ['id', 'name']


class SpecialtyDetailSerializer(serializers.ModelSerializer):
    doctor_count = serializers.SerializerMethodField()

    class Meta:
        model = Insurance
        fields = ['id', 'name', 'doctor_count']

    def get_doctor_count(self, specialty):
        return specialty.doctors.count()


class PatientSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source='user.phone')
    province = ProvinceSerializer()
    city = CitySerializer()
    insurance = InsuranceSerializer()
    age = serializers.SerializerMethodField()

    class Meta:
        model = Patient
        fields = ['id', 'user', 'first_name', 'last_name', 'gender', 'age',
                  'province', 'city', 'insurance', 'is_foreign_national', 
                  'national_code']

    def get_insurance(self, patient):
        if patient.insurance:
            return patient.insurance.name
        return None
    
    def get_age(self, patient):
        if patient.birth_date:
            return (date.today() - patient.birth_date).days // 365
        return None
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['gender'] = instance.get_gender_display()
        return representation


class PatientDetailSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source='user.phone', read_only=True)
    province = ProvinceSerializer()
    city = CitySerializer()
    insurance = InsuranceSerializer()
    age = serializers.SerializerMethodField()

    class Meta:
        model = Patient
        fields = ['id', 'user', 'first_name', 'last_name', 'gender', 'birth_date',
                  'age', 'email', 'insurance', 'is_foreign_national', 'national_code',
                  'province', 'city', 'case_history']
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['gender'] = instance.get_gender_display()
        return representation
    
    def get_age(self, patient):
        if patient.birth_date:
            return (date.today() - patient.birth_date).days // 365
        return None


class PatientUpdateSerializer(serializers.ModelSerializer):
    phone = serializers.CharField(source='user.phone', read_only=True)
    first_name = serializers.CharField(max_length=255)
    last_name = serializers.CharField(max_length=255)
    birth_date = serializers.DateField(format='%Y-%m-%d')
    gender = serializers.ChoiceField(choices=Patient.PERSON_GENDER)
    province = serializers.PrimaryKeyRelatedField(queryset=Province.objects.all())
    city = serializers.PrimaryKeyRelatedField(queryset=City.objects.all())

    class Meta:
        model = Patient
        fields = ['id', 'first_name', 'last_name', 'gender', 'birth_date', 
                  'is_foreign_national', 'national_code', 'province', 'city',
                  'phone', 'insurance', 'email']
        
    def validate_gender(self, gender):
        if gender not in [Patient.PERSON_GENDER_MALE, Patient.PERSON_GENDER_FEMALE]:
            raise serializers.ValidationError(_('Please choose your gender.'))
        return gender
    
    def validate_birth_date(self, birth_date):
        if birth_date > date.today():
            raise serializers.ValidationError(_("The date of birth entered is incorrect, today's date is %(today)s." % {'today': date.today()}))
        return birth_date        
        
    def validate(self, attrs):
        if 'national_code' not in attrs.keys() and not attrs.get('is_foreign_national'):
            raise serializers.ValidationError({'national_code': _('This field is required.')})

        instance = Patient(**attrs)

        try:
            instance.clean()
        except ValidationError as e:
            raise serializers.ValidationError({"detail": e.messages})

        return super().validate(attrs)
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['gender'] = instance.get_gender_display()
        return representation


class DoctorSpecialtySerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='specialty.id')
    name = serializers.CharField(source='specialty.name')

    class Meta:
        model = DoctorSpecialty
        fields = ['id', 'name']


class DoctorInsuranceSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='insurance.id')
    name = serializers.CharField(source='insurance.name')

    class Meta:
        model = DoctorInsurance
        fields = ['id', 'name']


class CommentSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    created_datetime = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S', read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'name', 'created_datetime', 'rating', 'is_suggest', 'waiting_time', 'body', 'is_anonymous']
        extra_kwargs = {
            'is_anonymous': {'write_only': True}
        }

    def get_name(self, comment):
        if comment.is_anonymous:
            return 'Anonymous user'
        return comment.patient.first_name

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['waiting_time'] = instance.get_waiting_time_display()
        return representation
    
    def create(self, validated_data):
        request = self.context.get('request')
        doctor = self.context.get('doctor')

        validated_data['patient'] = request.user.patient
        validated_data['doctor'] = doctor
        return super().create(validated_data)


class CommentDetailSerializer(serializers.ModelSerializer):
    patient = PatientSerializer()
    created_datetime = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S')

    class Meta:
        model = Comment
        fields = ['id', 'patient', 'created_datetime', 'rating', 'is_suggest', 'waiting_time', 'body', 'is_anonymous']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['waiting_time'] = instance.get_waiting_time_display()
        return representation
    

class DoctorSerializer(serializers.ModelSerializer):
    age = serializers.SerializerMethodField()
    province = ProvinceSerializer()
    city = CitySerializer()
    rating_average = serializers.SerializerMethodField()
    comment_count = serializers.SerializerMethodField()
    successful_reserve_count = serializers.SerializerMethodField()
    specialties = DoctorSpecialtySerializer(many=True)
    confirm_datetime = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S')
    is_cover_insurance = serializers.SerializerMethodField()
    first_free_reserve_datetime = serializers.SerializerMethodField()

    class Meta:
        model = Doctor
        fields = ['id', 'first_name', 'last_name', 'gender', 'age', 'status', 
                  'confirm_datetime', 'rating_average', 'comment_count', 
                  'successful_reserve_count', 'medical_council_number', 'specialties',
                  'first_free_reserve_datetime', 'is_cover_insurance', 'province', 'city', 
                  'office_address']
        
    def get_age(self, doctor):
        if doctor.birth_date:
            return (date.today() - doctor.birth_date).days // 365
        return None
    
    def get_rating_average(self, doctor):
        try:
            rating_average = round(sum([comment.rating for comment in doctor.comments.all()]) / doctor.comments.count(), 1)
            
            if rating_average == int(rating_average):
                return int(rating_average)
            return rating_average
        except ZeroDivisionError:
            return None

    def get_comment_count(self, doctor):
        return doctor.comments.count()
    
    def get_successful_reserve_count(self, doctor):
        return len(doctor.doctor_reserves)
    
    def get_is_cover_insurance(self, doctor):
        return bool(doctor.insurances.count())
    
    def get_first_free_reserve_datetime(self, doctor):
        free_reserves = doctor.doctor_free_reserves

        if free_reserves:
            today_date = date.today()
            first_free_reserve_date = free_reserves[0].reserve_datetime.date()

            if today_date == first_free_reserve_date:
                return _('Today')
            elif today_date + timedelta(days=1) == first_free_reserve_date:
                return _('Tomorrow')
            return first_free_reserve_date
        return None
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['gender'] = instance.get_gender_display()
        representation['status'] = instance.get_status_display()
        return representation
    

class DoctorAlternativeSerializer(serializers.ModelSerializer):
    specialties = DoctorSpecialtySerializer(many=True)
    city = CitySerializer()
    comment_rating_average = serializers.SerializerMethodField()
    comment_count = serializers.SerializerMethodField()
    successful_reserve_count = serializers.SerializerMethodField()
    first_free_reserve_date = serializers.SerializerMethodField()

    class Meta:
        model = Doctor
        fields = ['id', 'first_name', 'last_name', 'city', 'specialties',
                  'comment_rating_average', 'comment_count', 'successful_reserve_count', 'first_free_reserve_date']
    
    def get_comment_rating_average(self, doctor):
        try:
            rating_average = round(sum([comment.rating for comment in doctor.comments.all()]) / doctor.comments.count(), 1)
            
            if rating_average == int(rating_average):
                return int(rating_average)
            return rating_average
        except ZeroDivisionError:
            return None

    def get_comment_count(self, doctor):
        return doctor.comments.count()
    
    def get_successful_reserve_count(self, doctor):
        return len(doctor.doctor_reserves)
    
    def get_first_free_reserve_date(self, doctor):
        first_free_reserve = doctor.doctor_free_reserves[0]
        today_date = date.today()
        first_free_reserve_date = first_free_reserve.reserve_datetime.date()

        if today_date == first_free_reserve_date:
            return _('Today')
        elif today_date + timedelta(days=1) == first_free_reserve_date:
            return _('Tomorrow')
        return first_free_reserve_date
    

class DoctorDetailSerializer(serializers.ModelSerializer):
    phone = serializers.CharField(source='user.phone', read_only=True)
    age = serializers.SerializerMethodField()
    province = ProvinceSerializer()
    city = CitySerializer()
    comment_rating_average = serializers.SerializerMethodField()
    comment_count = serializers.SerializerMethodField()
    suggest_percentage = serializers.SerializerMethodField()
    average_waiting_time = serializers.SerializerMethodField()
    successful_reserve_count = serializers.SerializerMethodField()
    specialties = DoctorSpecialtySerializer(many=True)
    birth_date = serializers.DateField(format='%Y-%m-%d')
    confirm_datetime = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S')
    insurances = DoctorInsuranceSerializer(many=True)
    comments = CommentSerializer(many=True)
    alternative_doctors = serializers.SerializerMethodField()
    has_free_reserve = serializers.SerializerMethodField()
    first_free_reserve_datetime = serializers.SerializerMethodField()

    class Meta:
        model = Doctor
        fields = ['id', 'phone', 'first_name', 'last_name', 'gender', 'birth_date',
                  'age', 'email', 'status', 'confirm_datetime', 'comment_rating_average', 
                  'comment_count', 'suggest_percentage', 'average_waiting_time', 'successful_reserve_count',
                  'medical_council_number', 'specialties', 'national_code', 'insurances', 
                  'province', 'city', 'office_address', 'bio', 'has_free_reserve', 'first_free_reserve_datetime',
                  'alternative_doctors', 'comments']

    def get_age(self, doctor):
        if doctor.birth_date:
            return (date.today() - doctor.birth_date).days // 365
        return None

    def get_comment_rating_average(self, doctor):
        try:
            rating_average = round(sum([comment.rating for comment in doctor.comments.all()]) / doctor.comments.count(), 1)
            
            if rating_average == int(rating_average):
                return int(rating_average)
            return rating_average
        except ZeroDivisionError:
            return None

    def get_comment_count(self, doctor):
        return doctor.comments.count()

    def get_successful_reserve_count(self, doctor):
        return len(doctor.doctor_reserves)
    
    def get_suggest_percentage(self, doctor):
        try:
            return round((sum([1 for comment in doctor.comments.all() if comment.is_suggest]) / doctor.comments.count()) * 100)
        except ZeroDivisionError:
            return None
    
    def get_average_waiting_time(self, doctor):
        waiting_times = [comment.waiting_time for comment in doctor.comments.all()]

        if waiting_times:
            average_waiting_time = round(sum(waiting_times) / len(waiting_times))
            return dict(Comment.COMMENT_WAITING_TIME).get(average_waiting_time)
        return None
    
    def get_has_free_reserve(self, doctor):
        return bool(doctor.doctor_free_reserves)
    
    def get_first_free_reserve_datetime(self, doctor):
        if doctor.doctor_free_reserves:
            first_free_reserve = doctor.doctor_free_reserves[0]
            today_date = date.today()
            first_free_reserve_datetime = first_free_reserve.reserve_datetime

            if today_date == first_free_reserve_datetime.date():
                return _('Today') + ' ' + str(first_free_reserve_datetime.astimezone(TEHRAN_TZ).strftime('%m-%d %H:%M'))
            elif today_date + timedelta(days=1) == first_free_reserve_datetime.date():
                return _('Tomorrow') + ' ' + str(first_free_reserve_datetime.astimezone(TEHRAN_TZ).strftime('%m-%d %H:%M'))
            return str(first_free_reserve_datetime.astimezone(TEHRAN_TZ).strftime('%m-%d %H:%M'))
        return None
    
    def get_alternative_doctors(self, doctor):
        if bool(doctor.doctor_free_reserves):
            return []
        
        queryset = Doctor.objects.select_related('city').prefetch_related(
                Prefetch('specialties',
                             queryset=DoctorSpecialty.objects.select_related('specialty'))
                ).prefetch_related(
                   Prefetch('reserves',
                            queryset=Reserve.objects.filter(status=Reserve.RESERVE_STATUS_PAID),
                            to_attr='doctor_reserves')
                ).prefetch_related(
                    Prefetch('comments',
                             queryset=Comment.objects.filter(status=Comment.COMMENT_STATUS_APPROVED).select_related('patient').order_by('-created_datetime'))
                ).prefetch_related(
                    Prefetch('reserves',
                             queryset=Reserve.objects.filter(reserve_datetime__gte=datetime.now(tz=TEHRAN_TZ), patient__isnull=True).order_by('reserve_datetime'),
                             to_attr='doctor_free_reserves')
                ).filter(
                    specialties__specialty_id__in=doctor.specialties.values_list('specialty__id', flat=True), 
                    city=doctor.city,
                    reserves__reserve_datetime__gte=datetime.now(tz=TEHRAN_TZ),
                    reserves__status=Reserve.RESERVE_STATUS_UNPAID).\
                exclude(id=doctor.id).distinct()[:5]
        
        return DoctorAlternativeSerializer(queryset, many=True).data
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['gender'] = instance.get_gender_display()
        representation['status'] = instance.get_status_display()
        return representation


class DoctorCreateSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(max_length=255)
    last_name = serializers.CharField(max_length=255)
    national_code = serializers.CharField(max_length=10, validators=[NationalCodeValidator()])
    gender = serializers.ChoiceField(choices=Doctor.PERSON_GENDER)
    office_address = serializers.CharField()
    specialties_list = serializers.ListField(
        child=serializers.PrimaryKeyRelatedField(queryset=Specialty.objects.all()),
        write_only=True
    )
    specialties = DoctorSpecialtySerializer(many=True, read_only=True)
    insurances_list = serializers.ListField(
        child=serializers.PrimaryKeyRelatedField(queryset=Insurance.objects.all()),
        write_only=True,
        required=False
    )
    insurances = DoctorInsuranceSerializer(many=True, read_only=True)

    class Meta:
        model = Doctor
        fields = ['id', 'user', 'medical_council_number', 'first_name', 'last_name', 
                  'national_code', 'office_address', 'province', 'city', 'email', 
                  'gender', 'specialties_list', 'specialties', 'insurances_list', 'insurances']
        
    def validate_gender(self, gender):
        if gender not in [Doctor.PERSON_GENDER_MALE, Doctor.PERSON_GENDER_FEMALE]:
            raise serializers.ValidationError(_('Please choose your gender.'))
        return gender
    
    def validate_specialties_list(self, specialties_list):
        if not specialties_list:
            raise serializers.ValidationError(_('The doctor must have at least one specialty.'))
        return specialties_list
    
    def validate(self, attrs):
        new_attrs = {key:attrs.get(key) for key in attrs.keys() if key not in ['specialties_list', 'insurances_list']}
        instance = Doctor(**new_attrs)

        try:
            instance.clean()
        except ValidationError as e:
            raise serializers.ValidationError({"detail": e.messages})

        return super().validate(attrs)
    
    def create(self, validated_data):
        with transaction.atomic():
            specialties_list = validated_data.pop('specialties_list')
            insurances_list = validated_data.pop('insurances_list', [])

            doctor = Doctor.objects.create(
                **validated_data,
                status=Doctor.DOCTOR_STATUS_ACCEPTED,
                confirm_datetime=datetime.now(tz=TEHRAN_TZ)
            )

            for specialty in specialties_list:
                if DoctorSpecialty.objects.filter(doctor=doctor, specialty=specialty).exists():
                    raise serializers.ValidationError(
                        {'detail': _('The doctor %(doctor_full_name)s has already the specialty %(specialty_name)s.') % {'doctor_full_name': doctor.full_name, 'specialty_name': specialty.name}}
                    )
                DoctorSpecialty.objects.create(
                    specialty=specialty,
                    doctor=doctor
                )
            
            for insurance in insurances_list:
                if DoctorInsurance.objects.filter(doctor=doctor, insurance=insurance).exists():
                    raise serializers.ValidationError(
                        {'detail': _('The doctor %(doctor_full_name)s has already covers %(insurance_name)s insurance.') % {'doctor_full_name': doctor.full_name, 'insurance_name': insurance.name}}
                    )
                DoctorInsurance.objects.create(
                    insurance=insurance,
                    doctor=doctor
                )
            
            return doctor
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['gender'] = instance.get_gender_display()
        return representation


class DoctorUpdateSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(max_length=255)
    last_name = serializers.CharField(max_length=255)
    national_code = serializers.CharField(max_length=10, validators=[NationalCodeValidator()])
    gender = serializers.ChoiceField(choices=Doctor.PERSON_GENDER)
    office_address = serializers.CharField()
    specialties_list = serializers.ListField(
        child=serializers.PrimaryKeyRelatedField(queryset=Specialty.objects.all()),
        write_only=True
    )
    specialties = DoctorSpecialtySerializer(many=True, read_only=True)
    insurances_list = serializers.ListField(
        child=serializers.PrimaryKeyRelatedField(queryset=Insurance.objects.all()),
        write_only=True,
        required=False
    )
    insurances = DoctorInsuranceSerializer(many=True, read_only=True)

    class Meta:
        model = Doctor
        fields = ['id', 'medical_council_number', 'first_name', 'last_name', 
                  'national_code', 'office_address', 'province', 'city', 'email', 
                  'gender', 'specialties_list', 'specialties', 'insurances_list', 'insurances']
        
    def validate_gender(self, gender):
        if gender not in [Doctor.PERSON_GENDER_MALE, Doctor.PERSON_GENDER_FEMALE]:
            raise serializers.ValidationError(_('Please choose your gender.'))
        return gender
    
    def validate(self, attrs):
        new_attrs = {key:attrs.get(key) for key in attrs.keys() if key not in ['specialties_list', 'insurances_list']}
        instance = Doctor(**new_attrs)

        try:
            instance.clean()
        except ValidationError as e:
            raise serializers.ValidationError({'detail': e.messages})

        return super().validate(attrs)
    
    def update(self, instance, validated_data):
       with transaction.atomic():
            specialties_list = validated_data.pop('specialties_list', [])
            insurances_list = validated_data.pop('insurances_list', [])

            if specialties_list:
                instance.specialties.all().delete()

                for specialty in specialties_list:
                    if DoctorSpecialty.objects.filter(doctor=instance, specialty=specialty).exists():
                        raise serializers.ValidationError(
                            {'detail': _('The doctor %(doctor_full_name)s has already the specialty %(specialty_name)s.') % {'doctor_full_name': instance.full_name, 'specialty_name': specialty.name}}
                        )
                    DoctorSpecialty.objects.create(
                        specialty=specialty,
                        doctor=instance
                    )  
            if insurances_list:  
                instance.insurances.all().delete()   

                for insurance in insurances_list:
                    if DoctorInsurance.objects.filter(doctor=instance, insurance=insurance).exists():
                        raise serializers.ValidationError(
                            {'detail': _('The doctor %(doctor_full_name)s has already covers %(insurance_name)s insurance.') % {'doctor_full_name': instance.full_name, 'insurance_name': insurance.name}}
                        )
                    DoctorInsurance.objects.create(
                        insurance=insurance,
                        doctor=instance
                    )     

            return super().update(instance, validated_data)
       
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['gender'] = instance.get_gender_display()
        return representation


class ReservePatientSerializer(serializers.ModelSerializer):
    doctor = serializers.CharField(source='doctor.full_name')
    reserve_datetime = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S')
    is_expired = serializers.SerializerMethodField()

    class Meta:
        model = Reserve
        fields = ['id', 'doctor', 'status', 'price', 'reserve_datetime', 'is_expired']
    
    def get_is_expired(self, reserve):
        return True if reserve.reserve_datetime < datetime.now(tz=TEHRAN_TZ) else False

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['status'] = instance.get_status_display()
        return representation


class ReservePatientDetailSerializer(serializers.ModelSerializer):
    doctor = DoctorSerializer()
    reserve_datetime = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S')
    is_expired = serializers.SerializerMethodField()

    class Meta:
        model = Reserve
        fields = ['id', 'doctor', 'status', 'price', 'reserve_datetime', 'is_expired']
    
    def get_is_expired(self, reserve):
        return True if reserve.reserve_datetime < datetime.now(tz=TEHRAN_TZ) else False

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['status'] = instance.get_status_display()
        return representation


class ReservePatientUpdateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Reserve
        fields = ['id', 'status']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['status'] = instance.get_status_display()
        return representation


class CommentListWaitingPatientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Patient
        fields = ['id', 'first_name', 'last_name']


class CommentListWaitingDoctorSerializer(serializers.ModelSerializer):

    class Meta:
        model = Doctor
        fields = ['id', 'first_name', 'last_name']


class CommentListWaitingSerializer(serializers.ModelSerializer):
    patient = CommentListWaitingPatientSerializer()
    doctor = CommentListWaitingDoctorSerializer()
    created_datetime = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S')

    class Meta:
        model = Comment
        fields = ['id', 'patient', 'doctor', 'rating', 'is_suggest', 'waiting_time', 'is_anonymous', 'created_datetime']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['waiting_time'] = instance.get_waiting_time_display()
        return representation


class CommentListWaitingDetailSerializer(serializers.ModelSerializer):
    patient = CommentListWaitingPatientSerializer()
    doctor = CommentListWaitingDoctorSerializer()
    created_datetime = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S')

    class Meta:
        model = Comment
        fields = ['id', 'patient', 'doctor', 'rating', 'is_suggest', 'waiting_time', 'is_anonymous', 'created_datetime', 'body']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['waiting_time'] = instance.get_waiting_time_display()
        return representation


class CommentChangeStatusSerializer(serializers.ModelSerializer):

    class Meta:
        model = Comment
        fields = ['status']
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['status'] = instance.get_status_display()
        return representation


class ReserveDoctorSerializer(serializers.ModelSerializer):
    patient = serializers.SerializerMethodField()
    reserve_datetime = serializers.DateTimeField(format='%Y-%m-%d %H:%M')
    is_expired = serializers.SerializerMethodField()

    class Meta:
        model = Reserve
        fields = ['id', 'patient', 'status', 'price', 'reserve_datetime', 'is_expired']
    
    def get_patient(self, reserve):
        if reserve.patient:
            return reserve.patient.full_name
        return None
    
    def get_is_expired(self, reserve):
        return True if reserve.reserve_datetime < datetime.now(tz=TEHRAN_TZ) else False

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['status'] = instance.get_status_display()
        return representation


class ReserveDoctorDetailSerializer(serializers.ModelSerializer):
    patient = PatientSerializer()
    reserve_datetime = serializers.DateTimeField(format='%Y-%m-%d %H:%M')
    is_expired = serializers.SerializerMethodField()

    class Meta:
        model = Reserve
        fields = ['id', 'patient', 'status', 'price', 'reserve_datetime', 'is_expired']

    def get_is_expired(self, reserve):
        return True if reserve.reserve_datetime < datetime.now(tz=TEHRAN_TZ) else False

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['status'] = instance.get_status_display()
        return representation


class ReserveDoctorCreateSerializer(serializers.ModelSerializer):
    reserve_datetime = serializers.DateTimeField(format='%Y-%m-%d %H:%M')

    class Meta:
        model = Reserve
        fields = ['id', 'price', 'reserve_datetime']
    
    def validate_reserve_datetime(self, reserve_datetime):
        new_datetime = datetime.now(tz=TEHRAN_TZ) + timedelta(minutes=5)
        rounded_current_datetime = new_datetime.replace(second=0, microsecond=0)

        if rounded_current_datetime > reserve_datetime.replace(second=0, microsecond=0):
            raise serializers.ValidationError('The reserve datetime cannot be before %(rounded_current_datetime)s.' % {'rounded_current_datetime': rounded_current_datetime.strftime('%Y-%m-%d %H:%M')})
        return reserve_datetime.replace(second=0, microsecond=0)
    
    def validate(self, attrs):
        doctor = self.context.get('doctor')
        attrs['doctor'] = doctor
        instance = Reserve(**attrs)

        try:
            instance.clean()
        except ValidationError as e:
            raise serializers.ValidationError({'detail': e.messages})

        return super().validate(attrs)
        

class ReservePaymentQueryParamSerializer(serializers.Serializer):
    reserve_id = serializers.IntegerField(error_messages={
        'required': _('This query param is required.')
    })

    def validate(self, attrs):
        reserve_id = attrs.get('reserve_id')
        request = self.context.get('request')
        patient = request.user.patient

        try:
            reserve = Reserve.objects.get(id=reserve_id)
        except Reserve.DoesNotExist:
            raise NotFound({'detail': _("There isn't any reserve with this reserve_id.")})
        else:
            if reserve.reserve_datetime < datetime.now(tz=TEHRAN_TZ):
                raise serializers.ValidationError({'detail': _('This reserve has expired.')})
            elif reserve.patient and reserve.patient != patient:
                raise serializers.ValidationError({'detail': _('This reserve has been taken by another patient.')})
            elif reserve.patient and reserve.patient == patient and reserve.status == Reserve.RESERVE_STATUS_PAID:
                raise serializers.ValidationError({'detail': _('You have already taken and paid for this reserve.')})

        return attrs


class ReservePaymentSerializer(serializers.ModelSerializer):
    doctor = serializers.CharField(source='doctor.full_name')
    specialties = serializers.SerializerMethodField()
    patient = PatientSerializer()
    office_address = serializers.CharField(source='doctor.office_address')
    reserve_date = serializers.DateTimeField(source='reserve_datetime', format='%Y-%m-%d')
    reserve_time = serializers.DateTimeField(source='reserve_datetime', format='%H:%M:%S')

    class Meta:
        model = Reserve
        fields = ['id', 'doctor', 'specialties', 'reserve_date', 'reserve_time', 'price', 'office_address', 'patient']
    
    def get_specialties(self, reserve):
        serializer = DoctorSpecialtySerializer(reserve.doctor.specialties, many=True)
        return serializer.data


class RequestDoctorSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(max_length=255)
    last_name = serializers.CharField(max_length=255)
    national_code = serializers.CharField(max_length=10, validators=[NationalCodeValidator()])
    gender = serializers.ChoiceField(choices=Doctor.PERSON_GENDER)
    specialties_list = serializers.ListField(
        child=serializers.PrimaryKeyRelatedField(queryset=Specialty.objects.all()),
        write_only=True
    )

    class Meta:
        model = Doctor
        fields = ['id', 'medical_council_number', 'first_name', 'last_name', 
                  'national_code', 'email', 'gender', 'specialties_list']
        
    def validate_gender(self, gender):
        if gender not in [Doctor.PERSON_GENDER_MALE, Doctor.PERSON_GENDER_FEMALE]:
            raise serializers.ValidationError(_('Please choose your gender.'))
        return gender
    
    def validate_specialties_list(self, specialties_list):
        if not specialties_list:
            raise serializers.ValidationError(_('The doctor must have at least one specialty.'))
        return specialties_list
        
    def validate(self, attrs):
        request = self.context.get('request')

        if getattr(request.user, 'doctor', False) and request.user.doctor.status == Doctor.DOCTOR_STATUS_WAITING:
            raise serializers.ValidationError({'detail': _('You have already applied, your request is under review.')})

        return super().validate(attrs)
    
    def create(self, validated_data):
        with transaction.atomic():
            request = self.context.get('request')
            specialties_list = validated_data.pop('specialties_list')

            doctor = Doctor.objects.create(
                **validated_data,
                user=request.user
                )

            for specialty in specialties_list:
                if DoctorSpecialty.objects.filter(doctor=doctor, specialty=specialty).exists():
                    raise serializers.ValidationError(
                        {'detail': _('The doctor %(doctor_full_name)s has already the specialty %(specialty_name)s.') % {'doctor_full_name': doctor.full_name, 'specialty_name': specialty.name}}
                    )
                DoctorSpecialty.objects.create(
                    specialty=specialty,
                    doctor=doctor
                )

            return doctor


class DoctorListRequestSerializer(serializers.ModelSerializer):
    specialties = DoctorSpecialtySerializer(many=True)

    class Meta:
        model = Doctor
        fields = ['id', 'medical_council_number', 'first_name', 'last_name', 
                  'national_code', 'email', 'gender', 'specialties']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['gender'] = instance.get_gender_display()
        return representation


class DoctorListRequestUpdateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Doctor
        fields = ['id', 'status']
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['status'] = instance.get_status_display()
        return representation
    
    def update(self, instance, validated_data):
        validated_data['confirm_datetime'] = datetime.now(tz=TEHRAN_TZ)
        return super().update(instance, validated_data)
