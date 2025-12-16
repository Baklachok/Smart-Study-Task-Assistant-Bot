import logging
from aiogram import Bot, Dispatcher

from .config import settings
from .handlers import tasks

logging.basicConfig(level=logging.INFO)

bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
dp = Dispatcher()

# Регистрация обработчиков
dp.include_router(tasks.router)


async def on_startup():
    logging.info("Bot started")


if __name__ == "__main__":
    import asyncio

    asyncio.run(dp.start_polling(bot))
