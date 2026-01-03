from aiogram.types import Message
from aiogram.filters import Command
from aiogram import Router

from bot.commands import COMMANDS

router = Router()


@router.message(Command("help"))
async def help_command(message: Message):
    text = "📚 Доступные команды:\n\n"
    text += "\n".join(f"/{cmd.command} — {cmd.description}" for cmd in COMMANDS)
    await message.answer(text)
