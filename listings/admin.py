from django.contrib import admin

from .models import Listing


@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    list_display = ('title', 'owner', 'category', 'price', 'status', 'location', 'created_at')
    list_filter = ('category', 'status', 'location')
    search_fields = ('title', 'description', 'location')
