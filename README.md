# Smart Study & Task Assistant Bot

## Описание

Telegram-бот для управления задачами, учебными курсами и напоминаниями. Все данные хранятся в PostgreSQL, бизнес-логика
реализована на Django. Бот выступает в роли **thin client** и взаимодействует с backend через прямой доступ к Django ORM
и сервисным слоям.

Проект изначально спроектирован как **backend‑first** и готов к расширению под:

- Telegram Mini Apps (WebApp API)
- AI‑помощника
- REST API / Web интерфейс

---

## Стек технологий

- Python 3.12+
- Django 6.x
- PostgreSQL 15+
- aiogram 3.x
- Redis
- Celery + Celery Beat
- Docker + docker-compose
- Poetry
- OpenAI API

---

## Функциональность

- Авторизация пользователей через Telegram
- Управление задачами (создание, просмотр, завершение)
- Курсы и учебные темы с прогрессом
- Напоминания и отложенные задачи (Celery)
- Inline‑кнопки и FSM в Telegram
- Подготовка под Telegram Mini Apps
- AI‑помощник для задач и обучения

---

## Установка и запуск

### 1. Клонирование репозитория

```bash
git clone git@github.com:Baklachok/Smart-Study-Task-Assistant-Bot.git
cd DjangoProject
```

### 2. Создание `.env`

```env
SECRET_KEY=django-insecure-change-me
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,backend

POSTGRES_DB=smart_study_db
POSTGRES_USER=smart_study_user
POSTGRES_PASSWORD=smart_study_password
POSTGRES_HOST=postgres
POSTGRES_PORT=5432

REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

TELEGRAM_BOT_TOKEN=PUT_YOUR_TELEGRAM_BOT_TOKEN_HERE
```

---

### 3. Запуск через Docker

```bash
docker-compose up --build
```

### 4. Применение миграций

```bash
docker-compose exec backend python manage.py migrate
```

### 5. Создание суперпользователя (опционально)

```bash
docker-compose exec backend python manage.py createsuperuser
```

После запуска:

- Django доступен на `http://localhost:8000`
- Бот готов к работе в Telegram

---

## Команды Telegram‑бота

- `/start` — регистрация пользователя
- `/add_task` — добавить задачу
- `/tasks` — список задач
- `/tasks today` — задачи на сегодня
- `/tasks week` — задачи на неделю
- `/done <id>` — завершить задачу
- `/add_course` — добавить курс
- `/help` — помощь

---

## Структура проекта

```text
.
├── DjangoProject/          # Django project (settings, urls, wsgi)
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
├── manage.py
├── docker-compose.yaml
├── Dockerfile
├── pyproject.toml
├── poetry.lock
├── docs/
│   ├── architecture.md     # Архитектура проекта
│   └── tech_spec.md        # Техническое задание
└── README.md
```

> Бизнес‑приложения (users, tasks, courses, bot, reminders) добавляются как Django apps внутри проекта.

---

## Документация

- 📄 Техническое задание: `docs/tech_spec.md`
- 🏗 Архитектура: `docs/architecture.md`

