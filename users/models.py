from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):

    phone_number = models.CharField(max_length=20, blank=True)

    profile_image = models.ImageField(upload_to="profiles/", blank=True, null=True)

    is_verified = models.BooleanField(default=False)

    def __str__(self):
        return self.username
