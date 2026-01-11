import logging


class ContextFilter(logging.Filter):
    STANDARD_ATTRS = {
        "name",
        "msg",
        "args",
        "levelname",
        "levelno",
        "pathname",
        "filename",
        "module",
        "exc_info",
        "exc_text",
        "stack_info",
        "lineno",
        "funcName",
        "created",
        "msecs",
        "relativeCreated",
        "thread",
        "threadName",
        "processName",
        "process",
        "user_id",
        "email",
        "telegram_id",
    }

    def filter(self, record: logging.LogRecord) -> bool:
        # обязательный контекст
        record.user_id = getattr(record, "user_id", "-")
        record.email = getattr(record, "email", "-")
        record.telegram_id = getattr(record, "telegram_id", "-")

        # собираем dynamic extra
        record.extra = {
            k: v for k, v in record.__dict__.items() if k not in self.STANDARD_ATTRS
        } or "-"

        return True
