from django.contrib import admin

from .models import ContactMessage


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'email', 'subject', 'priority', 'status', 'created_at')
    list_filter = ('status', 'priority', 'subject', 'created_at')
    search_fields = ('full_name', 'email', 'phone', 'message')
    readonly_fields = ('created_at', 'updated_at')
