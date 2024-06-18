from django.utils.translation import gettext as _
from rest_framework import serializers

from .models import Province, City


class ProvinceSerializer(serializers.ModelSerializer):
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
            raise serializers.ValidationError(_('There is a city with this name in %(province_name)s.' % {'province_name': province.name}))

    def create(self, validated_data):
        province = self.context.get('province')
        return City.objects.create(province=province, **validated_data)
