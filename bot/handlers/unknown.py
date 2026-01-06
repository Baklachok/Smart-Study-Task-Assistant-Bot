from aiogram import Router, F
from aiogram.types import Message

router = Router()


@router.message(F.text.startswith("/"))
async def unknown_command_handler(message: Message):
    await message.answer(
        "❓ Неизвестная команда.\nВведи /help, чтобы посмотреть доступные команды."
    )


@router.message()
async def plain_text_handler(message: Message):
    await message.answer("🤖 Я работаю через команды.\nВведи /help, чтобы начать.")
