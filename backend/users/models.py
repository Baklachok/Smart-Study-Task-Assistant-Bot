import uuid
from typing import Optional, TypeVar, ClassVar

from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models

UserType = TypeVar("UserType", bound="User")


class UserManager(BaseUserManager[UserType]):
    use_in_migrations = True

    def create_user(
        self, telegram_id: int, password: Optional[str] = None, **extra_fields: object
    ) -> UserType:
        if not telegram_id:
            raise ValueError("Telegram ID must be set")
        user = self.model(telegram_id=telegram_id, **extra_fields)  # cast не нужен
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(
        self, telegram_id: int, password: Optional[str] = None, **extra_fields: object
    ) -> UserType:
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(telegram_id, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    id: ClassVar[models.UUIDField] = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False
    )
    telegram_id: ClassVar[models.BigIntegerField] = models.BigIntegerField(
        unique=True, db_index=True
    )
    username: ClassVar[models.CharField] = models.CharField(
        max_length=255, blank=True, null=True
    )
    first_name: ClassVar[models.CharField] = models.CharField(
        max_length=255, blank=True
    )
    language: ClassVar[models.CharField] = models.CharField(max_length=5, default="ru")
    timezone: ClassVar[models.CharField] = models.CharField(
        max_length=50, default="Europe/Moscow"
    )
    is_active: models.BooleanField = models.BooleanField(default=True)
    is_staff: models.BooleanField = models.BooleanField(default=False)
    created_at: models.DateTimeField = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = "telegram_id"
    REQUIRED_FIELDS: ClassVar[list[str]] = []

    def __str__(self) -> str:
        return f"{self.telegram_id}"
