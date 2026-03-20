from django.urls import path

from .views import (
    EmailLoginView,
    EmailRegisterView,
    LinkEmailView,
    MeView,
    TelegramLoginView,
    UserTokenRefreshView,
)

urlpatterns = [
    path("register/", EmailRegisterView.as_view(), name="users-register"),
    path("login/", EmailLoginView.as_view(), name="users-login"),
    path("link-email/", LinkEmailView.as_view(), name="users-link-email"),
    path("telegram-login/", TelegramLoginView.as_view(), name="users-telegram-login"),
    path("me/", MeView.as_view(), name="users-me"),
    path("token/refresh/", UserTokenRefreshView.as_view(), name="users-token-refresh"),
]
