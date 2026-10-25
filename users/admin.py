from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import EmailVerification, PhoneVerification, User


@admin.register(User)
class AssetLinkUserAdmin(UserAdmin):
    list_display = (
        'username',
        'email',
        'phone_number',
        'email_verified',
        'phone_verified',
        'is_verified',
        'is_active',
    )
    list_filter = (
        'email_verified',
        'phone_verified',
        'is_verified',
        'is_active',
        'is_staff',
    )
    fieldsets = UserAdmin.fieldsets + (
        ('Contact verification', {
            'fields': ('phone_number', 'email_verified', 'phone_verified', 'is_verified')
        }),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Contact details', {'fields': ('email', 'phone_number')}),
    )


@admin.register(PhoneVerification)
class PhoneVerificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'expires_at', 'failed_attempts', 'last_sent_at')
    search_fields = ('user__username', 'user__email', 'user__phone_number', 'provider_reference')
    readonly_fields = (
        'user',
        'code_hash',
        'provider_reference',
        'expires_at',
        'last_sent_at',
        'failed_attempts',
    )


@admin.register(EmailVerification)
class EmailVerificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'expires_at', 'failed_attempts', 'last_sent_at')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('user', 'code_hash', 'expires_at', 'last_sent_at', 'failed_attempts')
