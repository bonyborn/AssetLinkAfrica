from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    phone_number = models.CharField(
        max_length=20,
        blank=True
    )

    email_verified = models.BooleanField(default=False)
    phone_verified = models.BooleanField(default=False)

    profile_image = models.ImageField(
        upload_to='profiles/',
        blank=True,
        null=True
    )

    is_verified = models.BooleanField(
        default=False
    )

    def __str__(self):
        return self.username


class PhoneVerification(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='phone_verification'
    )
    code_hash = models.CharField(max_length=128, blank=True)
    provider_reference = models.CharField(max_length=128, blank=True)
    expires_at = models.DateTimeField()
    last_sent_at = models.DateTimeField()
    failed_attempts = models.PositiveSmallIntegerField(default=0)

    def __str__(self):
        return f'Phone verification for {self.user.username}'


class EmailVerification(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='email_verification'
    )
    code_hash = models.CharField(max_length=128)
    expires_at = models.DateTimeField()
    last_sent_at = models.DateTimeField()
    failed_attempts = models.PositiveSmallIntegerField(default=0)

    def __str__(self):
        return f'Email verification for {self.user.username}'
