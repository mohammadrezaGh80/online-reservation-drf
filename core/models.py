from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from uuid import uuid4
import random
import string

from .validators import PhoneValidator


class CustomUserManager(BaseUserManager):
    def create_user(self, phone, password=None, **extra_fields):
        if not phone:
            raise ValueError(_('Users must have a phone number.'))
        
        user = self.model(
            phone=phone,
            password=password,
            **extra_fields
        )

        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, phone, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        return self.create_user(phone, password, **extra_fields)
    

class CustomUser(AbstractBaseUser, PermissionsMixin):
    phone_validator = PhoneValidator()

    phone = models.CharField(max_length=11, unique=True, validators=[phone_validator], verbose_name=_('Phone'))

    is_active = models.BooleanField(
        default=True, verbose_name=_('Is active'),
        help_text=_(
            'Designates whether this user should be treated as active. '
            'Unselect this instead of deleting accounts.'
        )
    )
    is_staff = models.BooleanField(
        default=False, verbose_name=_('Is staff'), 
        help_text=_('Designates whether the user can log into this admin site.')
    )

    USERNAME_FIELD = 'phone'

    objects = CustomUserManager()

    def __str__(self):
        return self.phone

    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')


# default value for expired datetime otp
def get_expired_datetime():
    return timezone.now() + timezone.timedelta(seconds=120)


class OTP(models.Model):
    phone_validator = PhoneValidator()

    id = models.UUIDField(primary_key=True, default=uuid4, verbose_name=_('Request id'))
    phone = models.CharField(max_length=11, validators=[phone_validator], verbose_name=_('Phone'))
    password = models.CharField(max_length=4, verbose_name=_('Password'))

    created_datetime = models.DateTimeField(default=timezone.now, verbose_name=_('Created datetime'))
    expired_datetime = models.DateTimeField(default=get_expired_datetime , verbose_name=_('Expired datetime'))

    def generate_password(self):
        self.password = self._random_password()

    def _random_password(self):
        rand = random.SystemRandom()
        return ''.join(rand.choices(string.digits, k=4))   
    
    def __str__(self):
        return f'{self.phone}: {self.password}'
    
    class Meta:
        verbose_name = _('One time password')
        verbose_name_plural = _('One time passwords')
