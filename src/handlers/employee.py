from aiogram import Router, types
from aiogram.filters import Command

from src.database.models import Role
from src.handlers.access import require_role
from src.services.users import UserService

router = Router()
users = UserService()


@router.message(Command("employee_report"))
@require_role(Role.EMPLOYEE, Role.ADMIN)
async def employee_report_handler(message: types.Message) -> None:
    total = sum((await users.count_by_role()).values())
    await message.answer(
        "📋 Внутренний отчёт (доступ: сотрудник+):\n"
        f"- Активных пользователей бота: {total}\n"
        "- Заказов за сегодня: 12\n"
        "- Новых обращений: 3\n"
        "- Выручка за неделю: 84 300 руб."
    )
