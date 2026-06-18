from django.db import models

from bookings.models import Booking


class Payment(models.Model):

    PAYMENT_METHODS = (
        ("mpesa", "M-Pesa"),
        ("card", "Card"),
        ("bank", "Bank Transfer"),
    )

    booking = models.OneToOneField(Booking, on_delete=models.CASCADE)

    amount = models.DecimalField(max_digits=12, decimal_places=2)

    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)

    transaction_id = models.CharField(max_length=255, unique=True)

    is_paid = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.transaction_id
