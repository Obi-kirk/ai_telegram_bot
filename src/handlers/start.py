from aiogram import Router, types
from aiogram.filters import Command

router = Router()


@router.message(Command("start"))
async def start_handler(message: types.Message) -> None:
    await message.answer("Привет! Я твой AI-ассистент. Чем могу помочь?")
