from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from .models import OTP, CustomUser


# Custom Filter
class PasswordStatusFilter(admin.SimpleListFilter):
    title = 'password status'
    parameter_name = 'password'

    PASSWORD_EXPIRED = 'expired'
    PASSWORD_VALID = 'valid'

    def lookups(self, request, model_admin):
        return [
            (self.PASSWORD_EXPIRED, _('Expired')),
            (self.PASSWORD_VALID, _('Valid'))
        ]
    
    def queryset(self, request, queryset):
        if self.value() == self.PASSWORD_EXPIRED:
            return queryset.filter(expired_datetime__lt=timezone.now())
        elif self.value() == self.PASSWORD_VALID:
            return queryset.filter(expired_datetime__gte=timezone.now())


# Custom admin
@admin.register(CustomUser)
class CustomUserAdmin(BaseUserAdmin):
    model = CustomUser
    list_display = ['phone', 'is_active', 'is_staff']
    list_filter = ['is_active', 'is_superuser', 'is_staff']
    fieldsets = (
        (_('Personal info'), {'fields': ('phone', 'password', )}),
        (_('Permissions'), {'fields': ('is_active', 'is_superuser', 'is_staff', )})
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('phone', 'password1', 'password2')
        })
    )
    search_fields = ['phone']
    list_editable = ['is_active']
    readonly_fields = ['is_staff', 'is_superuser']
    ordering = []
    filter_horizontal = []
    list_per_page = 15


@admin.register(OTP)
class OTPAdmin(admin.ModelAdmin):
    list_display = ['phone', 'password', 'get_created_datetime', 'get_expired_datetime']
    ordering = ['-created_datetime']
    list_filter = [PasswordStatusFilter]
    list_per_page = 15

    @admin.display(description=_('created_datetime'))
    def get_created_datetime(self, otp):
        return otp.created_datetime.strftime('%Y:%m:%d %H:%M:%S')
    
    @admin.display(description=_('expired_datetime'))
    def get_expired_datetime(self, otp):
        return otp.expired_datetime.strftime('%Y:%m:%d %H:%M:%S')
