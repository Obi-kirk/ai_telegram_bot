import os

os.environ.setdefault("TESTING", "1")

from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from aiogram import Bot
from aiogram.client.session.base import BaseSession
from aiogram.methods.base import TelegramType
from aiogram.types import Chat, Message, Update
from aiogram.types import User as TgUser

from src.database.db import init_db


@pytest.fixture(autouse=True)
async def _db_ready() -> None:
    await init_db()


class FakeSession(BaseSession):
    """Записывает исходящие методы, ничего не отправляя."""

    def __init__(self) -> None:
        super().__init__()
        self.outbound: list[TelegramType] = []

    async def __call__(
        self, bot: Bot, method: TelegramType, timeout: int | None = None
    ) -> None:
        self.outbound.append(method)

    async def close(self) -> None:
        return None

    async def stream_content(self, url, timeout=None, chunk_size=65536):
        return SimpleNamespace()

    async def make_request(self, bot, method, timeout=None):
        return None


def make_update(user_id: int, text: str) -> Update:
    return Update(
        update_id=1,
        message=Message(
            message_id=1,
            date=datetime.now(timezone.utc),
            chat=Chat(id=user_id, type="private"),
            from_user=TgUser(id=user_id, is_bot=False, first_name="Test"),
            text=text,
        ),
    )


def sent_texts(session: FakeSession) -> list[str]:
    return [
        str(method.text)
        for method in session.outbound
        if hasattr(method, "text") and method.text
    ]
