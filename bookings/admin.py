from django.contrib import admin

from .models import Booking


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'listing', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = (
        'user__username',
        'user__email',
        'listing__title',
        'listing__location',
    )
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'
