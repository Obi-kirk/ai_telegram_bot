import os

from aiogram import Bot
from aiogram.types import BotCommand, BotCommandScopeChat, BotCommandScopeDefault
from dotenv import load_dotenv

load_dotenv()

USER_COMMANDS = [
    BotCommand(command="start", description="Приветствие"),
    BotCommand(command="about", description="О магазине"),
    BotCommand(command="catalog", description="Каталог по категориям"),
    BotCommand(command="cart", description="Корзина"),
    BotCommand(command="status", description="Статус заказов"),
    BotCommand(command="privacy", description="Политика конфиденциальности"),
    BotCommand(command="help", description="Помощь и список команд"),
]

ADMIN_COMMANDS = USER_COMMANDS + [
    BotCommand(command="setrole", description="Сменить роль пользователя"),
    BotCommand(command="block", description="Заблокировать пользователя"),
    BotCommand(command="unblock", description="Разблокировать пользователя"),
    BotCommand(command="admin_stats", description="Статистика пользователей"),
    BotCommand(command="employee_report", description="Внутренний отчёт"),
    BotCommand(command="orders", description="Список заказов"),
    BotCommand(command="order", description="Сменить статус заказа"),
]


def _admin_ids() -> list[int]:
    raw = os.getenv("ADMIN_IDS", "")
    return [int(v.strip()) for v in raw.split(",") if v.strip().isdigit()]


async def set_bot_commands(bot: Bot) -> None:
    """Устанавливает команды бота: базовые всем, админские — только админам."""
    await bot.set_my_commands(USER_COMMANDS, scope=BotCommandScopeDefault())
    for admin_id in _admin_ids():
        await bot.set_my_commands(
            ADMIN_COMMANDS, scope=BotCommandScopeChat(chat_id=admin_id)
        )
