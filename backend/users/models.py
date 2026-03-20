import uuid
from typing import ClassVar, Optional, TypeVar, cast

from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models

UserType = TypeVar("UserType", bound="User")


class UserManager(BaseUserManager[UserType]):
    use_in_migrations = True

    def create_user(
        self,
        email: str | None = None,
        password: Optional[str] = None,
        **extra_fields: object,
    ) -> UserType:
        telegram_id = cast(int | None, extra_fields.pop("telegram_id", None))
        normalized_email = email.strip().lower() if email else None

        if not normalized_email and telegram_id is None:
            raise ValueError("Either email or Telegram ID must be set")

        user = self.model(email=normalized_email, telegram_id=telegram_id, **extra_fields)
        if password is None:
            user.set_unusable_password()
        else:
            user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(
        self,
        email: str,
        password: Optional[str] = None,
        **extra_fields: object,
    ) -> UserType:
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if not email:
            raise ValueError("Superuser must have email set.")
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email=email, password=password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    id: ClassVar[models.UUIDField] = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False
    )
    telegram_id: ClassVar[models.BigIntegerField] = models.BigIntegerField(
        unique=True, db_index=True, null=True, blank=True
    )
    email: ClassVar[models.EmailField] = models.EmailField(
        unique=True, db_index=True, null=True, blank=True
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
    email_verified: models.BooleanField = models.BooleanField(default=False)
    created_at: models.DateTimeField = models.DateTimeField(auto_now_add=True)
    last_habits_report_at: models.DateTimeField = models.DateTimeField(
        null=True, blank=True
    )

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: ClassVar[list[str]] = []

    def __str__(self) -> str:
        if self.email:
            return self.email
        if self.telegram_id is not None:
            return str(self.telegram_id)
        return str(self.id)
