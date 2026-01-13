from django.apps import AppConfig


class TasksConfig(AppConfig):
    name = "tasks"

    def ready(self) -> None:
        import tasks.signals  # noqa
