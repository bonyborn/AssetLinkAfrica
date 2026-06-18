from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    model = User
    fieldsets = UserAdmin.fieldsets + (
        ("Profile", {"fields": ("phone_number", "profile_image", "is_verified")}),
    )
    list_display = ("username", "email", "is_verified", "is_staff", "is_active")
