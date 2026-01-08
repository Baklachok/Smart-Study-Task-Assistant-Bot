from aiogram import Router, F
from aiogram.types import Message

router = Router()


@router.message(F.text.startswith("/"))  # type: ignore
async def unknown_command_handler(message: Message) -> None:
    await message.answer(
        "❓ Неизвестная команда.\nВведи /help, чтобы посмотреть доступные команды."
    )


@router.message()  # type: ignore
async def plain_text_handler(message: Message) -> None:
    await message.answer("🤖 Я работаю через команды.\nВведи /help, чтобы начать.")
