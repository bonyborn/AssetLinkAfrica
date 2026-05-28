from django.db import models
from django.conf import settings


class Listing(models.Model):

    CATEGORY_CHOICES = (
        ('car', 'Car'),
        ('land', 'Land'),
    )

    STATUS_CHOICES = (
        ('available', 'Available'),
        ('booked', 'Booked'),
    )

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='listings'
    )

    title = models.CharField(max_length=255)

    description = models.TextField()

    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES
    )

    price = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    location = models.CharField(
        max_length=255
    )

    image = models.ImageField(
        upload_to='listings/'
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='available'
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.title
