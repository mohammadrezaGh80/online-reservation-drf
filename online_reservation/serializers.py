from django.utils.translation import gettext as _
from django.core.exceptions import ValidationError
from rest_framework import serializers

from datetime import date

from .models import Insurance, Patient, Province, City


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
    insurance = serializers.SerializerMethodField()
    age = serializers.SerializerMethodField()

    class Meta:
        model = Patient
        fields = ['id', 'user', 'first_name', 'last_name', 'gender', 'age',
                  'insurance', 'is_foreign_national', 'national_code']

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
    first_name = serializers.CharField(max_length=255, label=_('First name'))
    last_name = serializers.CharField(max_length=255, label=_('Last name'))
    birth_date = serializers.DateField(format='%Y-%m-%d', label=_('Birth date'))
    gender = serializers.ChoiceField(choices=Patient.PERSON_GENDER)
    province = serializers.PrimaryKeyRelatedField(queryset=Province.objects.all(), label=_('Province'))
    city = serializers.PrimaryKeyRelatedField(queryset=City.objects.all(), label=_('City'))

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
