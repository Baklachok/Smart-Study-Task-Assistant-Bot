import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand

from bot.commands import COMMANDS
from bot.config import settings
from bot.handlers import tasks, courses, help, topics, unknown, start

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def setup_bot_commands(bot: Bot, retries: int = 5, delay: float = 2.0) -> None:
    """Регистрируем команды бота с повторной попыткой"""
    for attempt in range(1, retries + 1):
        try:
            await bot.set_my_commands(
                [
                    BotCommand(command=cmd.command, description=cmd.description)
                    for cmd in COMMANDS
                ]
            )
            logger.info("Команды зарегистрированы")
            return
        except Exception as e:
            logger.warning(f"Попытка {attempt}/{retries} не удалась: {e}")
            await asyncio.sleep(delay)
    logger.error("Не удалось зарегистрировать команды после нескольких попыток")


async def main() -> None:
    bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
    dp = Dispatcher()

    dp.include_router(start.router)
    dp.include_router(tasks.router)
    dp.include_router(courses.router)
    dp.include_router(help.router)
    dp.include_router(topics.router)
    dp.include_router(unknown.router)

    await setup_bot_commands(bot)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
