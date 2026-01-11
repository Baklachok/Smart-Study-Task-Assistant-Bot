LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "context": {"()": "core.logging.ContextFilter"},
    },
    "formatters": {
        "default": {
            "format": (
                "[{levelname}] {asctime} "
                "user_id={user_id} email={email} tg={telegram_id} "
                "{name}: {message} | extra={extra}"
            ),
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "filters": ["context"],
            "formatter": "default",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "DEBUG",
    },
}
