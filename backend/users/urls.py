from django.urls import path

from .views import MeView, TelegramLoginView, UserTokenRefreshView

urlpatterns = [
    path("telegram-login/", TelegramLoginView.as_view()),
    path("me/", MeView.as_view()),
    path("token/refresh/", UserTokenRefreshView.as_view()),
]
