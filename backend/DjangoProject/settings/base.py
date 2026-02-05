import os
from pathlib import Path


def _env_bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).lower() == "true"


def _env_float(name: str, default: float) -> float:
    return float(os.getenv(name, str(default)))


def _env_int(name: str, default: int) -> int:
    return int(os.getenv(name, str(default)))


BASE_DIR = Path(__file__).resolve().parent.parent


DEBUG = _env_bool("DEBUG", False)
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "").split(",")

DJANGO_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.admin",
    "django_filters",
    "django_celery_beat",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "drf_spectacular",
]

LOCAL_APPS = [
    "users",
    "tasks",
    "courses",
    "topics",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "DjangoProject.urls"
WSGI_APPLICATION = "DjangoProject.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("POSTGRES_DB"),
        "USER": os.getenv("POSTGRES_USER"),
        "PASSWORD": os.getenv("POSTGRES_PASSWORD"),
        "HOST": os.getenv("POSTGRES_HOST"),
        "PORT": os.getenv("POSTGRES_PORT"),
    }
}

AUTH_USER_MODEL = "users.User"

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = os.getenv("LANGUAGE_CODE", "ru")
TIME_ZONE = os.getenv("TIME_ZONE", "Europe/Moscow")
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_BEAT_SCHEDULE = {
    "send-task-reminders": {
        "task": "tasks.tasks.send_task_reminders",
        "schedule": 60.0,
    },
    "send-habits-reports": {
        "task": "tasks.tasks.send_weekly_habits_reports",
        "schedule": 604800.0,
    },
}

BOT_SEND_MESSAGE_TASK = os.getenv("BOT_SEND_MESSAGE_TASK", "bot.send_message")
BOT_QUEUE = os.getenv("BOT_QUEUE", "telegram")

# Hugging Face LLM settings
HUGGINGFACE_ENABLED = _env_bool("HUGGINGFACE_ENABLED", False)
HUGGINGFACE_API_TOKEN = os.getenv("HUGGINGFACE_API_TOKEN")
HUGGINGFACE_MODEL = os.getenv("HUGGINGFACE_MODEL")
HUGGINGFACE_API_BASE = os.getenv(
    "HUGGINGFACE_API_BASE",
    "https://router.huggingface.co/v1/chat/completions",
)
HUGGINGFACE_TIMEOUT = _env_float("HUGGINGFACE_TIMEOUT", 8)
HUGGINGFACE_MAX_NEW_TOKENS = _env_int("HUGGINGFACE_MAX_NEW_TOKENS", 240)
HUGGINGFACE_RETRIES = _env_int("HUGGINGFACE_RETRIES", 1)
HUGGINGFACE_USE_LLM_WEEKLY = _env_bool("HUGGINGFACE_USE_LLM_WEEKLY", True)
