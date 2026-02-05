# Smart Study & Task Assistant Bot

Telegram-бот и REST API для управления задачами, курсами и учебными темами.
Бизнес-логика реализована на Django REST Framework, бот на aiogram работает как thin client и общается с API по HTTP.

---

## Возможности

- Регистрация пользователей через Telegram
- Интерактивное меню (inline-кнопки, редактирование одного сообщения)
- Управление задачами (создание, просмотр, завершение, удаление)
- Курсы и темы с прогрессом
- Напоминания о задачах (Celery + Redis)
- Аналитика привычек (LLM через HuggingFace, опционально)
- Еженедельная сводка привычек (Celery Beat)
- JWT-аутентификация
- Swagger/Redoc документация API

---

## Архитектура

```
Telegram → aiogram Bot → Django REST API → PostgreSQL
                         ↘ Celery + Redis → bot Celery worker → Telegram API (напоминания)
```

---

## Стек

- Python 3.12+
- Django + Django REST Framework
- PostgreSQL 15+
- aiogram 3.x
- Redis 7
- Celery + Celery Beat
- drf-spectacular (OpenAPI/Swagger)
- SimpleJWT
- Docker + docker-compose
- Poetry

---

## Быстрый старт (Docker)

### 1. Клонирование

```bash
git clone git@github.com:Baklachok/Smart-Study-Task-Assistant-Bot.git
cd DjangoProject
```

### 2. Создание `.env`

Минимально необходимый набор переменных:

```env
SECRET_KEY=django-insecure-change-me
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,backend

POSTGRES_DB=smart_study_db
POSTGRES_USER=smart_study_user
POSTGRES_PASSWORD=smart_study_password
POSTGRES_HOST=postgres
POSTGRES_PORT=5432

CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

TELEGRAM_BOT_TOKEN=PUT_YOUR_TELEGRAM_BOT_TOKEN_HERE
API_URL=http://backend:8000/api/v1
BOT_SEND_MESSAGE_TASK=bot.send_message
BOT_QUEUE=telegram

# HuggingFace LLM (опционально)
HUGGINGFACE_ENABLED=true
HUGGINGFACE_API_TOKEN=YOUR_TOKEN
HUGGINGFACE_MODEL=YOUR_MODEL_ID
HUGGINGFACE_API_BASE=https://router.huggingface.co/v1/chat/completions
HUGGINGFACE_TIMEOUT=8
HUGGINGFACE_MAX_NEW_TOKENS=240
HUGGINGFACE_RETRIES=1
HUGGINGFACE_USE_LLM_WEEKLY=true
```

Опционально:

```env
LANGUAGE_CODE=ru
TIME_ZONE=Europe/Moscow
```

### 3. Запуск

```bash
docker-compose up --build
```

`backend` автоматически выполняет `migrate` при старте.

---

## Доступные сервисы

- API: `http://localhost:8000/api/v1`
- Swagger UI: `http://localhost:8000/api/schema/swagger/`
- Redoc: `http://localhost:8000/api/schema/redoc/`
- Flower (Celery): `http://localhost:5555`

---

## Команды Telegram-бота

- `/start` — регистрация пользователя
- `/menu` — открыть меню
- `/add_task` — создать задачу
- `/tasks` — список задач (`today` | `week`)
- `/habits` — аналитика привычек
- `/add_course` — добавить курс
- `/courses` — список курсов
- `/add_topic` — добавить тему
- `/topics` — список тем
- `/help` — помощь

---

## Локальная разработка (без Docker)

1. Установить зависимости:

```bash
poetry install
```

2. Задать переменные окружения (см. блок `.env` выше).

3. Запуск backend:

```bash
python backend/manage.py migrate
python backend/manage.py runserver
```

4. Запуск бота:

```bash
python -m bot.bot
```

5. Запуск Celery:

```bash
celery -A DjangoProject.celery worker -l info
celery -A DjangoProject.celery beat -l info
```

---

## Документация

- Техническое задание: `docs/tech_spec.md`
- Архитектура: `docs/architecture.md`
