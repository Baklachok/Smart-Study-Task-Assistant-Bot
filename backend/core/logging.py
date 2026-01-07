import logging


class ContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "user_id"):
            record.user_id = "-"
        if not hasattr(record, "email"):
            record.email = "-"
        if not hasattr(record, "telegram_id"):
            record.telegram_id = "-"
        return True
