from typing import Any, cast

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from .models import Task
from topics.models import Topic


@receiver(post_save, sender=Task)
def update_topic_progress_on_save(
    sender: type[Task],
    instance: Task,
    **kwargs: Any,
) -> None:
    if not instance.topic:
        return

    topic = cast(Topic, instance.topic)
    topic.recalc_progress()


@receiver(post_delete, sender=Task)
def update_topic_progress_on_delete(
    sender: type[Task],
    instance: Task,
    **kwargs: Any,
) -> None:
    if not instance.topic:
        return

    topic = cast(Topic, instance.topic)
    topic.recalc_progress()
