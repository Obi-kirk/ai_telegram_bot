from aiogram import Router, types
from aiogram.filters import Command

from src.handlers.shop import MAIN_MENU

router = Router()


@router.message(Command("start"))
async def start_handler(message: types.Message) -> None:
    await message.answer(
        "Привет! Я бот-консультант «Кузница Северного Ветра». Выберите действие:",
        reply_markup=MAIN_MENU,
    )
