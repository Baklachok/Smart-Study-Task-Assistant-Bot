from celery import Celery

from bot.config import settings

celery_app = Celery("bot", broker=settings.CELERY_BROKER_URL)

celery_app.conf.update(
    task_default_queue=settings.BOT_QUEUE,
    task_routes={
        "bot.send_message": {"queue": settings.BOT_QUEUE},
    },
)

celery_app.autodiscover_tasks(["bot"], related_name="celery_tasks")
