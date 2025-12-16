import uuid

from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.utils.timezone import now


class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    telegram_id = models.BigIntegerField(
        unique=True,
        db_index=True
    )

    username = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    first_name = models.CharField(
        max_length=255,
        blank=True
    )

    language = models.CharField(
        max_length=5,
        default="en"
    )

    timezone = models.CharField(
        max_length=50,
        default="UTC"
    )

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    created_at = models.DateTimeField(default=now)

    USERNAME_FIELD = "telegram_id"
    REQUIRED_FIELDS = []

    def __str__(self):
        return f"{self.telegram_id}"
