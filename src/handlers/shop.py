from aiogram import F, Router, types
from aiogram.filters import Command
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from src.database.models import CartItem, User
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
    "- /cart — корзина (кнопки для изменения)\n"
    "- /cart add <артикул> [кол-во] — добавить товар\n"
    "- /cart clear — очистить корзину\n"
    "- /status — статус заказов\n"
    "- /help — помощь\n\n"
    "Задавайте вопросы в свободной форме — я найду ответ в базе знаний."
)


def _cart_keyboard(items: list[CartItem]) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(text="−", callback_data=f"cart:dec:{item.article}"),
            InlineKeyboardButton(
                text=f"{item.title} x{item.qty}",
                callback_data="cart:noop",
            ),
            InlineKeyboardButton(text="+", callback_data=f"cart:inc:{item.article}"),
        ]
        for item in items
    ]
    rows.append(
        [InlineKeyboardButton(text="Оформить заказ", callback_data="cart:checkout")]
    )
    rows.append(
        [InlineKeyboardButton(text="Очистить корзину", callback_data="cart:clear")]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


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
    if not items:
        await message.answer(cart.format(items))
        return
    await message.answer(cart.format(items), reply_markup=_cart_keyboard(items))


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


@router.callback_query(F.data.startswith("cart:"))
async def cart_callback(callback: CallbackQuery, user: User) -> None:
    parts = callback.data.split(":")
    action = parts[1]
    if callback.message is None:
        await callback.answer("Сообщение устарело")
        return

    if action == "inc":
        await cart.change_qty(user.telegram_id, parts[2], 1)
        await callback.answer("+1")
    elif action == "dec":
        await cart.change_qty(user.telegram_id, parts[2], -1)
        await callback.answer("-1")
    elif action == "noop":
        await callback.answer()
        return
    elif action == "clear":
        await cart.clear(user.telegram_id)
        await callback.answer("Корзина очищена")
        await _render_cart(callback, user)
        return
    elif action == "checkout":
        items = await cart.list_items(user.telegram_id)
        if not items:
            await callback.answer("Корзина пуста")
            return
        confirm = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="Подтвердить заказ", callback_data="cart:confirm"
                    ),
                    InlineKeyboardButton(text="Отмена", callback_data="cart:cancel"),
                ]
            ]
        )
        await callback.message.edit_text(
            f"Оформить заказ на {cart.total(items):,} руб.?".replace(",", " "),
            reply_markup=confirm,
        )
        await callback.answer()
        return
    elif action == "confirm":
        result = await cart.checkout(user.telegram_id)
        await callback.message.edit_text(result)
        await callback.answer()
        return
    elif action == "cancel":
        await callback.answer()
        await _render_cart(callback, user)
        return
    await _render_cart(callback, user)


async def _render_cart(callback: CallbackQuery, user: User) -> None:
    items = await cart.list_items(user.telegram_id)
    if not items:
        await callback.message.edit_text(cart.format(items))
    else:
        await callback.message.edit_text(
            cart.format(items), reply_markup=_cart_keyboard(items)
        )
