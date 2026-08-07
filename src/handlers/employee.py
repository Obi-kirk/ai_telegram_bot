from aiogram import Router, types
from aiogram.filters import Command

from src.database.models import OrderStatus, Role
from src.handlers.access import require_role
from src.services.cart import OrderService
from src.services.users import UserService

router = Router()
users = UserService()
orders = OrderService()

_VALID_STATUSES = {status.value for status in OrderStatus}


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


@router.message(Command("order"))
@require_role(Role.EMPLOYEE, Role.ADMIN)
async def order_handler(message: types.Message) -> None:
    args = message.text.split()
    if len(args) != 3 or not args[1].isdigit():
        await message.answer(
            "Формат: /order <id> <статус>\n"
            f"Статусы: {', '.join(sorted(_VALID_STATUSES))}"
        )
        return
    status = args[2].strip().lower()
    if status not in _VALID_STATUSES:
        await message.answer(
            f"Неизвестный статус {status}. Допустимо: "
            f"{', '.join(sorted(_VALID_STATUSES))}"
        )
        return

    order = await orders.set_status(int(args[1]), status)
    if order is None:
        await message.answer(f"Заказ #{args[1]} не найден")
        return
    await message.answer(
        f"Заказ #{order.id} ({order.total:,} руб.) → статус обновлён".replace(",", " ")
    )


@router.message(Command("orders"))
@require_role(Role.EMPLOYEE, Role.ADMIN)
async def orders_handler(message: types.Message) -> None:
    all_orders = await orders.list_all()
    if not all_orders:
        await message.answer("Заказов пока нет.")
        return
    lines = [f"Всего заказов: {len(all_orders)}"]
    lines.append(orders.format(all_orders))
    await message.answer("\n".join(lines))
