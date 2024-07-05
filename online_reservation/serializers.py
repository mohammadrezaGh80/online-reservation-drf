from django.utils.translation import gettext as _
from django.core.exceptions import ValidationError
from django.db import transaction
from rest_framework import serializers

from datetime import date, datetime

from .models import Doctor, DoctorSpecialty, Insurance, Patient, Province, City, Reserve, Specialty, DoctorInsurance, Comment
from .validators import NationalCodeValidator


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
    patients_count = serializers.SerializerMethodField()

    class Meta:
        model = Insurance
        fields = ['id', 'name', 'patients_count']

    def get_patients_count(self, insurance):
        return insurance.patients.count()


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
    created_datetime = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S')

    class Meta:
        model = Comment
        fields = ['id', 'name', 'created_datetime', 'rating', 'is_suggest', 'waiting_time', 'body']

    def get_name(self, comment):
        if comment.is_anonymous:
            return 'Anonymous user'
        return comment.patient.first_name

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

    class Meta:
        model = Doctor
        fields = ['id', 'first_name', 'last_name', 'gender', 'age', 'status', 
                  'confirm_datetime', 'rating_average', 'comment_count', 
                  'successful_reserve_count', 'medical_council_number', 'specialties',
                  'is_cover_insurance', 'province', 'city', 'office_address']
        
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
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['gender'] = instance.get_gender_display()
        representation['status'] = instance.get_status_display()
        return representation
    

class DoctorDetailSerializer(serializers.ModelSerializer):
    phone = serializers.CharField(source='user.phone', read_only=True)
    age = serializers.SerializerMethodField()
    province = ProvinceSerializer()
    city = CitySerializer()
    rating_average = serializers.SerializerMethodField()
    comment_count = serializers.SerializerMethodField()
    suggest_percentage = serializers.SerializerMethodField()
    average_waiting_time = serializers.SerializerMethodField()
    successful_reserve_count = serializers.SerializerMethodField()
    specialties = DoctorSpecialtySerializer(many=True)
    birth_date = serializers.DateField(format='%Y-%m-%d')
    confirm_datetime = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S')
    insurances = DoctorInsuranceSerializer(many=True)
    comments = CommentSerializer(many=True)

    class Meta:
        model = Doctor
        fields = ['id', 'phone', 'first_name', 'last_name', 'gender', 'birth_date',
                  'age', 'email', 'status', 'confirm_datetime', 'rating_average', 
                  'comment_count', 'suggest_percentage', 'average_waiting_time', 'successful_reserve_count',
                  'medical_council_number', 'specialties', 'national_code', 'insurances', 
                  'province', 'city', 'office_address', 'bio', 'comments']
        
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
            insurances_list = validated_data.pop('insurances_list', None)

            doctor = Doctor.objects.create(
                **validated_data,
                status=Doctor.DOCTOR_STATUS_ACCEPTED,
                confirm_datetime=datetime.now()
            )

            for specialty in specialties_list:
                if DoctorSpecialty.objects.filter(doctor=doctor, specialty=specialty).exists():
                    raise serializers.ValidationError(
                        {'detail': _('The doctor %(doctor_full_name)s has already the specialty %(specialty_name)s') % {'doctor_full_name': doctor.full_name, 'specialty_name': specialty.name}}
                    )
                DoctorSpecialty.objects.create(
                    specialty=specialty,
                    doctor=doctor
                )
            
            for insurance in insurances_list:
                if DoctorInsurance.objects.filter(doctor=doctor, insurance=insurance).exists():
                    raise serializers.ValidationError(
                        {'detail': _('The doctor %(doctor_full_name)s has already covers %(insurance_name)s insurance') % {'doctor_full_name': doctor.full_name, 'insurance_name': insurance.name}}
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
            raise serializers.ValidationError({"detail": e.messages})

        return super().validate(attrs)
    
    def update(self, instance, validated_data):
       with transaction.atomic():
            specialties_list = validated_data.pop('specialties_list', None)
            insurances_list = validated_data.pop('insurances_list', None)

            if specialties_list:
                instance.specialties.all().delete()

                for specialty in specialties_list:
                    if DoctorSpecialty.objects.filter(doctor=instance, specialty=specialty).exists():
                        raise serializers.ValidationError(
                            {'detail': _('The doctor %(doctor_full_name)s has already the specialty %(specialty_name)s') % {'doctor_full_name': instance.full_name, 'specialty_name': specialty.name}}
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
                            {'detail': _('The doctor %(doctor_full_name)s has already covers %(insurance_name)s insurance') % {'doctor_full_name': instance.full_name, 'insurance_name': insurance.name}}
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

    class Meta:
        model = Reserve
        fields = ['id', 'doctor', 'status', 'price', 'reserve_datetime']
        read_only_fields = ['status']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['status'] = instance.get_status_display()
        return representation


class ReservePatientDetailSerializer(serializers.ModelSerializer):
    doctor = DoctorSerializer()
    reserve_datetime = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S')

    class Meta:
        model = Reserve
        fields = ['id', 'doctor', 'status', 'price', 'reserve_datetime']
        read_only_fields = ['status']

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
