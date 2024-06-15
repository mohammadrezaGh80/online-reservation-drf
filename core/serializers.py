from django.utils.translation import gettext as _
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import OTP


User = get_user_model()


class OTPSerializer(serializers.ModelSerializer):
    request_id = serializers.CharField(source='id', read_only=True)

    class Meta:
        model = OTP
        fields = ['request_id', 'phone']
        extra_kwargs = {
            'phone': {'write_only': True}
        }

    def create(self, validated_data):
        otp = OTP()
        otp.phone = validated_data.get('phone')
        otp.generate_password()
        otp.save()
        return otp


class VerifyOTPSerializer(serializers.ModelSerializer):
    request_id = serializers.UUIDField(source='id', label=_('Request id'))

    class Meta:
        model = OTP
        fields = ['request_id', 'phone', 'password'] 


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ['id', 'phone']


class UserDetailSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ['id', 'phone', 'is_active', 'is_staff', 'is_superuser']
        read_only_fields = ['phone']
    
    def validate_is_staff(self, is_staff):
        if is_staff:
            user = self.instance
            if not user.has_usable_password():
                raise serializers.ValidationError(_('User(phone number: %(phone_number)s) does not have a password, please enter a password for the user.') % {'phone_number': user.phone})

        return is_staff
    
    def validate_is_superuser(self, is_superuser):
        if is_superuser:
            user = self.instance
            if not user.has_usable_password():
                raise serializers.ValidationError(_('User(phone number: %(phone_number)s) does not have a password, please enter a password for the user.') % {'phone_number': user.phone})

        return is_superuser


class SetPasswordSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        max_length=128,
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        label=_('Password')
    )

    class Meta:
        model = User
        fields = ['password']

    def validate(self, attrs):
        password = attrs.get('password', None)
        validate_password(password)
        return attrs
    
    def update(self, instance, validated_data):
        password = validated_data.get('password')
        instance.set_password(password)
        instance.save(update_fields=['password'])
        return instance
