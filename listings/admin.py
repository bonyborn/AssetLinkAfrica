from django.contrib import admin

from .models import Listing, ListingImage, Subscription, SubscriptionPlan


class ListingImageInline(admin.TabularInline):
    model = ListingImage
    extra = 0


@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    inlines = (ListingImageInline,)
    list_display = (
        'title',
        'public_id',
        'owner',
        'category',
        'listing_type',
        'verification_status',
        'price',
        'location',
        'status',
        'expires_at',
        'created_at',
    )
    list_filter = (
        'category',
        'listing_type',
        'verification_status',
        'status',
        'created_at',
    )
    search_fields = (
        'public_id',
        'title',
        'description',
        'location',
        'vehicle_make',
        'vehicle_model',
        'owner__username',
        'owner__email',
    )
    readonly_fields = ('public_id', 'created_at', 'updated_at')
    date_hierarchy = 'created_at'


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = (
        'code',
        'minimum_listings',
        'maximum_listings',
        'monthly_price',
        'is_active',
    )
    list_filter = ('is_active', 'code')


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan', 'status', 'starts_at', 'ends_at')
    list_filter = ('status', 'plan')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('created_at',)
