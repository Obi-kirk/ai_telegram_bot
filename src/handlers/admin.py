from aiogram import Router, types
from aiogram.filters import Command

from src.database.models import Role, User, UserStatus
from src.handlers.access import require_role
from src.services.users import UserService
from src.utils.sanitize import parse_role

router = Router()
users = UserService()


@router.message(Command("setrole"))
@require_role(Role.ADMIN)
async def setrole_handler(message: types.Message, user: User) -> None:
    args = message.text.split()
    if len(args) != 3:
        await message.answer(
            "Формат: /setrole <id или @username> <user|employee|admin>"
        )
        return
    target, role_raw = args[1], args[2]

    role = parse_role(role_raw)
    if role is None:
        await message.answer("Роль должна быть: user, employee или admin")
        return

    victim = await users.resolve_user(target)
    if victim is None:
        await message.answer(f"Пользователь {target} не найден")
        return
    if victim.telegram_id == user.telegram_id:
        await message.answer("Нельзя изменить собственную роль")
        return

    await users.set_role(victim.telegram_id, role)
    await message.answer(
        f"Роль пользователя {victim.username or victim.telegram_id} изменена на {role.value}"
    )


@router.message(Command("block"))
@require_role(Role.ADMIN)
async def block_handler(message: types.Message, user: User) -> None:
    await _set_blocked(message, user, True)


@router.message(Command("unblock"))
@require_role(Role.ADMIN)
async def unblock_handler(message: types.Message, user: User) -> None:
    await _set_blocked(message, user, False)


async def _set_blocked(message: types.Message, user: User, blocked: bool) -> None:
    args = message.text.split()
    if len(args) != 2:
        await message.answer(
            f"Формат: /{'block' if blocked else 'unblock'} <id или @username>"
        )
        return

    victim = await users.resolve_user(args[1])
    if victim is None:
        await message.answer(f"Пользователь {args[1]} не найден")
        return
    if victim.telegram_id == user.telegram_id:
        await message.answer("Нельзя заблокировать себя")
        return

    status = UserStatus.BLOCKED if blocked else UserStatus.ACTIVE
    await users.set_status(victim.telegram_id, status)
    await message.answer(
        f"Пользователь {victim.username or victim.telegram_id} "
        f"{'заблокирован' if blocked else 'разблокирован'}"
    )


@router.message(Command("admin_stats"))
@require_role(Role.ADMIN)
async def admin_stats_handler(message: types.Message) -> None:
    stats = await users.count_by_role()
    all_users = await users.list_all()
    total = sum(stats.values())
    lines = [f"Всего пользователей: {total}"]
    for role in (Role.USER, Role.EMPLOYEE, Role.ADMIN):
        lines.append(f"{role.value}: {stats.get(role.value, 0)}")
    lines.append("\nСписок:")
    for u in all_users:
        name = f"@{u.username}" if u.username else "—"
        lines.append(f"{u.telegram_id} | {name} | {u.role} | {u.status}")
    await message.answer("📊 Статистика:\n" + "\n".join(lines))
