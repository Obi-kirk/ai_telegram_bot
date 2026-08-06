from aiogram import Router, types
from aiogram.filters import Command

from src.database.models import User
from src.services.cart import CartService, OrderService
from src.services.catalog import CatalogService

router = Router()
catalog = CatalogService()
cart = CartService()
orders = OrderService()

_HELP_TEXT = (
    "Доступные команды:\n"
    "- /start — приветствие\n"
    "- /catalog — каталог по категориям\n"
    "- /cart — корзина\n"
    "- /cart add <артикул> [кол-во] — добавить товар\n"
    "- /cart clear — очистить корзину\n"
    "- /cart checkout — оформить заказ\n"
    "- /status — статус заказов\n"
    "- /help — помощь\n\n"
    "Задавайте вопросы в свободной форме — я найду ответ в базе знаний."
)


@router.message(Command("help"))
async def help_handler(message: types.Message) -> None:
    await message.answer(_HELP_TEXT)


@router.message(Command("catalog"))
async def catalog_handler(message: types.Message) -> None:
    for category, products in catalog.by_category():
        await message.answer(catalog.format_category(category, products))


@router.message(Command("cart"))
async def cart_handler(message: types.Message, user: User) -> None:
    args = message.text.split()
    if len(args) > 1:
        await _cart_command(message, user.telegram_id, args[1:])
        return
    items = await cart.list_items(user.telegram_id)
    await message.answer(cart.format(items))


async def _cart_command(
    message: types.Message, telegram_id: int, args: list[str]
) -> None:
    sub, rest = args[0].lower(), args[1:]
    if sub == "add" and rest:
        qty = 1
        if len(rest) > 1 and rest[1].isdigit():
            qty = int(rest[1])
        await message.answer(await cart.add(telegram_id, rest[0], qty))
    elif sub == "clear":
        await cart.clear(telegram_id)
        await message.answer("Корзина очищена.")
    elif sub == "checkout":
        result = await cart.checkout(telegram_id)
        await message.answer(result)
    else:
        await message.answer("Формат: /cart add <артикул> [кол-во] | clear | checkout")


@router.message(Command("status"))
async def status_handler(message: types.Message, user: User) -> None:
    user_orders = await orders.list_by_user(user.telegram_id)
    await message.answer(orders.format(user_orders))
