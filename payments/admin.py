from django.contrib import admin

from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        "transaction_id",
        "booking",
        "amount",
        "payment_method",
        "is_paid",
        "created_at",
    )
    list_filter = ("payment_method", "is_paid")
    search_fields = ("transaction_id", "booking__listing__title")
