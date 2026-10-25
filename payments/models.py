from django.db import models
from django.conf import settings
from django.db.models import Q
from bookings.models import Booking
from listings.models import Subscription, SubscriptionPlan


class Payment(models.Model):

    STATUS_PENDING = 'pending'
    STATUS_PAID = 'paid'
    STATUS_FAILED = 'failed'

    STATUS_CHOICES = (
        (STATUS_PENDING, 'Pending'),
        (STATUS_PAID, 'Paid'),
        (STATUS_FAILED, 'Failed'),
    )

    PAYMENT_METHODS = (
        ('mpesa', 'M-Pesa'),
        ('card', 'Card'),
        ('bank', 'Bank Transfer'),
    )

    booking = models.OneToOneField(
        Booking,
        on_delete=models.CASCADE
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHODS
    )

    transaction_id = models.CharField(
        max_length=255,
        unique=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING
    )

    phone_number = models.CharField(
        max_length=15,
        blank=True,
        default=''
    )

    checkout_request_id = models.CharField(
        max_length=255,
        unique=True,
        null=True,
        blank=True
    )

    receipt_number = models.CharField(
        max_length=64,
        unique=True,
        null=True,
        blank=True
    )

    result_description = models.CharField(
        max_length=255,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.transaction_id


class SubscriptionPayment(models.Model):

    STATUS_PENDING = 'pending'
    STATUS_PAID = 'paid'
    STATUS_FAILED = 'failed'

    STATUS_CHOICES = (
        (STATUS_PENDING, 'Pending'),
        (STATUS_PAID, 'Paid'),
        (STATUS_FAILED, 'Failed'),
    )

    PAYMENT_METHODS = Payment.PAYMENT_METHODS

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='subscription_payments'
    )

    plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.PROTECT,
        related_name='payments'
    )

    subscription = models.ForeignKey(
        Subscription,
        on_delete=models.SET_NULL,
        related_name='payments',
        null=True,
        blank=True,
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHODS
    )

    transaction_id = models.CharField(
        max_length=255,
        unique=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING
    )

    phone_number = models.CharField(
        max_length=15,
        blank=True,
        default=''
    )

    checkout_request_id = models.CharField(
        max_length=255,
        unique=True,
        null=True,
        blank=True
    )

    stripe_session_id = models.CharField(
        max_length=255,
        unique=True,
        null=True,
        blank=True
    )

    stripe_payment_intent_id = models.CharField(
        max_length=255,
        blank=True,
        default=''
    )

    receipt_number = models.CharField(
        max_length=64,
        unique=True,
        null=True,
        blank=True
    )

    bank_transfer_reference = models.CharField(
        max_length=100,
        blank=True,
        default=''
    )

    result_description = models.CharField(
        max_length=255,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-created_at',)
        constraints = [
            models.UniqueConstraint(
                fields=('user',),
                condition=Q(status='pending'),
                name='one_pending_subscription_payment_per_user',
            ),
        ]

    def __str__(self):
        return f'{self.transaction_id} - {self.get_payment_method_display()}'
