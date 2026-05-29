from django.contrib import admin

from .models import Booking


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('user', 'listing', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('user__username', 'listing__title')
