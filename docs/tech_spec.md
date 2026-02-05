# Tech Spec: Smart Study & Task Assistant Bot

## 1. Общая информация

### 1.1 Назначение системы

Система предназначена для управления задачами, учебными курсами и напоминаниями через Telegram-бот. Вся бизнес-логика
реализуется на сервере (Django + DRF), Telegram-бот является клиентом API.

### 1.2 Целевая аудитория

- Студенты
- Начинающие разработчики
- Пользователи, ведущие учебные и личные задачи в Telegram

### 1.3 Стек технологий

- Python 3.12+
- Django 5.x
- Django REST Framework
- PostgreSQL 15+
- aiogram 3.x
- Docker + docker-compose
- Redis + Celery
- drf-spectacular (OpenAPI/Swagger)
- SimpleJWT

## 2. Архитектура системы

### 2.1 Общая схема

- Django REST API — основной backend
- aiogram — клиент API Telegram
- PostgreSQL — единое хранилище данных
- Celery + Redis — фоновые задачи и напоминания

### 2.2 Принципы

- Telegram-бот не содержит бизнес-логики
- API проектируется независимо от Telegram
- Все сущности принадлежат пользователю

## 3. Пользовательские сценарии

### 3.1 Регистрация пользователя

- Пользователь отправляет `/start`
- Бот передает данные в API
- Backend создает пользователя или возвращает существующего
- Бот открывает интерактивное меню

### 3.2 Управление задачами

- Добавление: `/add_task Название | 2025-12-20 18:00 | high`
- Просмотр: `/tasks`, `/tasks today`, `/tasks week`

### 3.3 Курсы и темы

- Добавление курса: `/add_course Python Backend`
- Добавление темы: `/add_topic Django ORM | course_id`
- Связь задач с темами и курсами

### 3.4 Напоминания

- Автоматическое создание при создании задачи
- Отправка через Celery с учетом таймзоны

### 3.5 Аналитика привычек

- Отчет по привычкам: `/habits`
- LLM-аналитика через HuggingFace (опционально)
- Еженедельная сводка отправляется Celery Beat

## 4. Функциональные требования

### 4.1 Пользователи (модель `User`)

| Поле        | Тип        | Описание         |
|-------------|------------|------------------|
| id          | UUID       | Идентификатор    |
| telegram_id | BIGINT     | Telegram ID      |
| username    | VARCHAR    | Username         |
| first_name  | VARCHAR    | Имя              |
| language    | VARCHAR(5) | Язык             |
| timezone    | VARCHAR    | Таймзона         |
| created_at  | DATETIME   | Дата регистрации |
| last_habits_report_at | DATETIME | Дата последней сводки |

### 4.2 Задачи (модель `Task`)

| Поле        | Тип                           |
|-------------|-------------------------------|
| id          | UUID                          |
| user        | FK(User)                      |
| title       | VARCHAR                       |
| description | TEXT                          |
| due_at      | DATETIME                      |
| status      | ENUM(pending, done, canceled) |
| priority    | ENUM(low, medium, high)       |
| created_at  | DATETIME                      |
| completed_at | DATETIME                     |

### 4.3 Курсы и темы

**Course**

| Поле        | Тип      |
|-------------|----------|
| id          | UUID     |
| user        | FK(User) |
| title       | VARCHAR  |
| description | TEXT     |

**Topic**

| Поле     | Тип         |
|----------|-------------|
| id       | UUID        |
| course   | FK(Course)  |
| title    | VARCHAR     |
| progress | INT (0–100) |

### 4.4 Напоминания (модель `Reminder`)

| Поле      | Тип      |
|-----------|----------|
| id        | UUID     |
| task      | FK(Task) |
| notify_at | DATETIME |
| sent      | BOOLEAN  |

## 5. API (DRF)

### 5.1 Авторизация

- По `telegram_id`

### 5.2 Эндпоинты

**Пользователь:**

```
POST /api/v1/users/telegram-login/
GET  /api/v1/users/me/
```

**Задачи:**

```
POST   /api/v1/tasks/
GET    /api/v1/tasks/
GET    /api/v1/tasks/habits/
PATCH  /api/v1/tasks/{id}/
DELETE /api/v1/tasks/{id}/
```

**Курсы:**

```
POST /api/v1/courses/
GET  /api/v1/courses/
```

**Темы:**

```
POST /api/v1/topics/
GET  /api/v1/topics/
```

## 6. Telegram Bot

### 6.1 Команды

| Команда     | Описание         |
|-------------|------------------|
| /start      | Регистрация      |
| /menu       | Меню             |
| /add_task   | Создание задачи  |
| /tasks      | Список задач     |
| /habits     | Аналитика привычек |
| /add_course | Добавить курс    |
| /courses    | Список курсов    |
| /add_topic  | Добавить тему    |
| /topics     | Список тем       |
| /help       | Помощь           |

### 6.2 Inline-кнопки

- Завершить задачу
- Удалить задачу
- Показать детали

## 7. Нефункциональные требования

- Время ответа API ≤ 300 мс
- PEP8 стиль кода
- Логирование ошибок
- Graceful shutdown

## 8. Инфраструктура

- Docker Compose:
    - backend
    - postgres
    - redis
    - celery_worker
    - celery_beat
    - flower
    - bot

## 9. Логи и мониторинг

- Django logging
