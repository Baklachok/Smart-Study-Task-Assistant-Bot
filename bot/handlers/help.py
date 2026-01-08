from aiogram.types import Message
from aiogram.filters import Command
from aiogram import Router

from bot.commands import COMMANDS

router = Router()


@router.message(Command("help"))  # type: ignore
async def help_command(message: Message) -> None:
    text = "📚 Доступные команды:\n\n"
    text += "\n".join(f"/{cmd.command} — {cmd.description}" for cmd in COMMANDS)
    await message.answer(text)
