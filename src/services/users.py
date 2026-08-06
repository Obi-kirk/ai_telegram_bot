import os

from sqlalchemy import func, select

from src.database.db import session_factory
from src.database.models import Role, User, UserStatus
from src.utils.sanitize import parse_user_target


def _admin_ids() -> set[int]:
    raw = os.getenv("ADMIN_IDS", "")
    return {int(x) for x in raw.split(",") if x.strip().isdigit()}


class UserService:
    """Работа с пользователями: создание, роли, статусы."""

    async def get_or_create(
        self, telegram_id: int, username: str | None = None
    ) -> User:
        async with session_factory() as session:
            user = await session.scalar(
                select(User).where(User.telegram_id == telegram_id)
            )
            if user:
                if username and user.username != username:
                    user.username = username
                    await session.commit()
                return user

            role = Role.ADMIN.value if telegram_id in _admin_ids() else Role.USER.value
            user = User(telegram_id=telegram_id, username=username, role=role)
            session.add(user)
            await session.commit()
            return user

    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        async with session_factory() as session:
            return await session.scalar(
                select(User).where(User.telegram_id == telegram_id)
            )

    async def resolve_user(self, target: str) -> User | None:
        """Находит пользователя по '@username' или числовому ID."""
        parsed = parse_user_target(target)
        if not parsed:
            return None
        kind, value = parsed
        async with session_factory() as session:
            if kind == "id":
                return await session.scalar(
                    select(User).where(User.telegram_id == value)
                )
            return await session.scalar(
                select(User).where(User.username == value.lower())
            )

    async def set_role(self, telegram_id: int, role: Role) -> User | None:
        async with session_factory() as session:
            user = await session.scalar(
                select(User).where(User.telegram_id == telegram_id)
            )
            if user:
                user.role = role.value
                await session.commit()
            return user

    async def set_status(self, telegram_id: int, status: UserStatus) -> User | None:
        async with session_factory() as session:
            user = await session.scalar(
                select(User).where(User.telegram_id == telegram_id)
            )
            if user:
                user.status = status.value
                await session.commit()
            return user

    async def count_by_role(self) -> dict[str, int]:
        async with session_factory() as session:
            rows = await session.execute(
                select(User.role, func.count()).group_by(User.role)
            )
            return dict(rows.all())
