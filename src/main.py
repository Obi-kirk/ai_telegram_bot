import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.types import ErrorEvent
from dotenv import load_dotenv

from src.database.db import init_db
from src.handlers.access import UserMiddleware
from src.handlers.admin import router as admin_router
from src.handlers.employee import router as employee_router
from src.handlers.message import router as message_router
from src.handlers.shop import router as shop_router
from src.handlers.start import router as start_router

load_dotenv()

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)


def _get_token() -> str:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN не задан в .env")
    return token


def create_dispatcher() -> Dispatcher:
    dp = Dispatcher()
    user_middleware = UserMiddleware()
    dp.message.outer_middleware(user_middleware)
    dp.callback_query.outer_middleware(user_middleware)
    dp.include_router(start_router)
    dp.include_router(admin_router)
    dp.include_router(employee_router)
    dp.include_router(shop_router)
    dp.include_router(message_router)

    @dp.errors()
    async def error_handler(event: ErrorEvent) -> None:
        logger.error("Ошибка обработки: %s", event.exception)

    return dp


async def main() -> None:
    await init_db()
    bot = Bot(token=_get_token())
    dp = create_dispatcher()
    logger.info("Бот запущен, начинаю polling")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
