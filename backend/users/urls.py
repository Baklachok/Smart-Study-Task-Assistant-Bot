from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import TelegramLoginView, MeView

urlpatterns = [
    path("telegram-login/", TelegramLoginView.as_view()),
    path("me/", MeView.as_view()),
    path("token/refresh/", TokenRefreshView.as_view()),
]
