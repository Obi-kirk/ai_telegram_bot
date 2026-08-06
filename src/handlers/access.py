from collections.abc import Awaitable, Callable
from inspect import signature
from typing import Any

from aiogram import BaseMiddleware, types
from aiogram.types import TelegramObject

from src.database.models import Role, User, UserStatus
from src.services.users import UserService

FORBIDDEN_TEXT = "⛔ Нет доступа. Эта команда недоступна для вашей роли."


class UserMiddleware(BaseMiddleware):
    """Поднимает пользователя из БД на каждый апдейт, игнорирует заблокированных."""

    def __init__(self) -> None:
        self.users = UserService()

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user = (
            event.from_user
            if isinstance(event, (types.Message, types.CallbackQuery))
            else None
        )
        if user is None:
            return await handler(event, data)

        db_user = await self.users.get_or_create(user.id, user.username)
        if db_user.status == UserStatus.BLOCKED.value:
            return None
        data["user"] = db_user
        return await handler(event, data)


def require_role(*roles: Role) -> Callable:
    """Допускает к хендлеру только пользователей с одной из указанных ролей."""

    allowed = {role.value for role in roles}

    def decorator(handler: Callable) -> Callable:
        async def wrapper(
            event: types.Message | types.CallbackQuery, **kwargs: Any
        ) -> Any:
            user: User | None = kwargs.get("user")
            if user is None or user.role not in allowed:
                await event.answer(FORBIDDEN_TEXT)
                return None
            allowed_params = signature(handler).parameters
            filtered = {k: v for k, v in kwargs.items() if k in allowed_params}
            return await handler(event, **filtered)

        return wrapper

    return decorator
