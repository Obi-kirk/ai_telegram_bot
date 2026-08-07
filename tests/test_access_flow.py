import pytest
from aiogram import Bot, Dispatcher
from sqlalchemy import delete

from src.database.db import session_factory
from src.database.models import Role, User, UserStatus
from src.main import create_dispatcher
from src.services.users import UserService
from tests.conftest import FakeSession, make_update, sent_texts

TEST_IDS = {900100001, 900100002, 900100003, 900100004, 900100005, 900100006}
users = UserService()

dp = create_dispatcher()


@pytest.fixture
async def bot_dp():
    session = FakeSession()
    bot = Bot(token="123456:TESTTOKEN", session=session)
    yield bot, dp, session
    async with session_factory() as db:
        await db.execute(delete(User).where(User.telegram_id.in_(TEST_IDS)))
        await db.commit()


async def _run(bot: Bot, dp: Dispatcher, user_id: int, text: str) -> None:
    await dp.feed_update(bot, make_update(user_id, text))


class TestAdminStats:
    async def test_regular_user_denied(self, bot_dp) -> None:
        bot, dp, session = bot_dp
        await users.get_or_create(900100001)
        await _run(bot, dp, 900100001, "/admin_stats")
        assert sent_texts(session) == [
            "⛔ Нет доступа. Эта команда недоступна для вашей роли."
        ]

    async def test_employee_denied(self, bot_dp) -> None:
        bot, dp, session = bot_dp
        await users.get_or_create(900100001)
        await users.set_role(900100001, Role.EMPLOYEE)
        await _run(bot, dp, 900100001, "/admin_stats")
        assert "Нет доступа" in sent_texts(session)[0]

    async def test_admin_allowed(self, bot_dp) -> None:
        bot, dp, session = bot_dp
        await users.get_or_create(900100002)
        await users.set_role(900100002, Role.ADMIN)
        await _run(bot, dp, 900100002, "/admin_stats")
        text = sent_texts(session)[0]
        assert "Статистика" in text
        assert "user:" in text


class TestEmployeeReport:
    async def test_regular_user_denied(self, bot_dp) -> None:
        bot, dp, session = bot_dp
        await users.get_or_create(900100003)
        await _run(bot, dp, 900100003, "/employee_report")
        assert "Нет доступа" in sent_texts(session)[0]

    async def test_employee_allowed(self, bot_dp) -> None:
        bot, dp, session = bot_dp
        await users.get_or_create(900100003)
        await users.set_role(900100003, Role.EMPLOYEE)
        await _run(bot, dp, 900100003, "/employee_report")
        assert "Внутренний отчёт" in sent_texts(session)[0]

    async def test_admin_allowed(self, bot_dp) -> None:
        bot, dp, session = bot_dp
        await users.get_or_create(900100002)
        await users.set_role(900100002, Role.ADMIN)
        await _run(bot, dp, 900100002, "/employee_report")
        assert "Внутренний отчёт" in sent_texts(session)[0]


class TestBlockedUser:
    async def test_blocked_user_fully_ignored(self, bot_dp) -> None:
        bot, dp, session = bot_dp
        await users.get_or_create(900100004)
        await users.set_status(900100004, UserStatus.BLOCKED)
        await _run(bot, dp, 900100004, "/admin_stats")
        assert session.outbound == []


class TestSetRole:
    async def test_admin_sets_employee(self, bot_dp) -> None:
        bot, dp, session = bot_dp
        await users.get_or_create(900100005)
        await users.set_role(900100005, Role.ADMIN)
        await users.get_or_create(900100006)
        await _run(bot, dp, 900100005, "/setrole 900100006 employee")
        assert "изменена на employee" in sent_texts(session)[0]
        victim = await users.get_by_telegram_id(900100006)
        assert victim.role == Role.EMPLOYEE.value

    async def test_admin_cannot_change_own_role(self, bot_dp) -> None:
        bot, dp, session = bot_dp
        await users.get_or_create(900100005)
        await users.set_role(900100005, Role.ADMIN)
        await _run(bot, dp, 900100005, "/setrole 900100005 user")
        assert "Нельзя изменить собственную роль" in sent_texts(session)[0]

    async def test_regular_user_denied(self, bot_dp) -> None:
        bot, dp, session = bot_dp
        await users.get_or_create(900100001)
        await _run(bot, dp, 900100001, "/setrole 900100006 employee")
        assert "Нет доступа" in sent_texts(session)[0]

    async def test_invalid_role_rejected(self, bot_dp) -> None:
        bot, dp, session = bot_dp
        await users.get_or_create(900100005)
        await users.set_role(900100005, Role.ADMIN)
        await _run(bot, dp, 900100005, "/setrole 900100006 boss")
        assert "Роль должна быть" in sent_texts(session)[0]


class TestPrivacy:
    async def test_privacy_shown_to_any_user(self, bot_dp) -> None:
        bot, dp, session = bot_dp
        await users.get_or_create(900100001)
        await _run(bot, dp, 900100001, "/privacy")
        text = sent_texts(session)[0]
        assert "тестовый бот" in text
        assert "не передаются третьим лицам" in text
        assert "не несёт ответственности" in text
