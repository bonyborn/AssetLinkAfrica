from django.contrib import admin
from django.contrib import messages

from .models import Payment, SubscriptionPayment
from .subscriptions import activate_subscription_payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'booking',
        'amount',
        'payment_method',
        'status',
        'receipt_number',
        'created_at',
    )
    list_filter = ('status', 'payment_method', 'created_at')
    search_fields = (
        'transaction_id',
        'checkout_request_id',
        'receipt_number',
        'phone_number',
        'booking__user__username',
        'booking__listing__title',
    )
    readonly_fields = (
        'booking',
        'amount',
        'payment_method',
        'transaction_id',
        'status',
        'phone_number',
        'checkout_request_id',
        'receipt_number',
        'result_description',
        'created_at',
    )
    date_hierarchy = 'created_at'

    def has_add_permission(self, _request):
        return False


@admin.register(SubscriptionPayment)
class SubscriptionPaymentAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'plan',
        'subscription',
        'amount',
        'payment_method',
        'status',
        'bank_transfer_reference',
        'receipt_number',
        'created_at',
    )
    list_filter = ('status', 'payment_method', 'plan', 'created_at')
    search_fields = (
        'transaction_id',
        'checkout_request_id',
        'stripe_session_id',
        'bank_transfer_reference',
        'receipt_number',
        'user__username',
        'user__email',
    )
    readonly_fields = (
        'user',
        'plan',
        'subscription',
        'amount',
        'payment_method',
        'transaction_id',
        'status',
        'phone_number',
        'checkout_request_id',
        'stripe_session_id',
        'stripe_payment_intent_id',
        'receipt_number',
        'bank_transfer_reference',
        'result_description',
        'created_at',
        'updated_at',
    )
    date_hierarchy = 'created_at'
    actions = ('verify_bank_transfers',)

    @admin.action(description='Verify selected bank transfers')
    def verify_bank_transfers(self, request, queryset):
        verified = 0
        skipped = 0
        for payment in queryset:
            if (
                payment.payment_method != 'bank'
                or payment.status != SubscriptionPayment.STATUS_PENDING
                or not payment.bank_transfer_reference
            ):
                skipped += 1
                continue
            try:
                activate_subscription_payment(payment.pk)
            except ValueError:
                skipped += 1
                continue
            self.log_change(
                request,
                payment,
                'Bank transfer reference verified; subscription activated.',
            )
            verified += 1

        if verified:
            self.message_user(
                request,
                f'{verified} bank transfer(s) verified and subscription(s) activated.',
                messages.SUCCESS,
            )
        if skipped:
            self.message_user(
                request,
                f'{skipped} payment(s) skipped; only pending bank transfers with references can be verified.',
                messages.WARNING,
            )

    def has_add_permission(self, request):
        return False
