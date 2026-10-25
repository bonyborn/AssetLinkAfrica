from django.db import models
from django.db.models import Q
from django.conf import settings
from listings.models import Listing


class Booking(models.Model):

    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    listing = models.ForeignKey(
        Listing,
        on_delete=models.CASCADE
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=('listing',),
                condition=Q(status__in=('pending', 'approved')),
                name='one_active_booking_per_listing',
            ),
        ]

    def __str__(self):
        return f"{self.user} - {self.listing}"
