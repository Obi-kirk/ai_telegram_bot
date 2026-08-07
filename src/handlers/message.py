from aiogram import Router, types
from aiogram.enums import ChatAction
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from src.database.models import User
from src.services.catalog import Product
from src.services.history import dialog_memory
from src.services.matcher import ProductMatcher
from src.services.rag_answers import RAGAnswerService
from src.utils.markdown import to_telegram_html

router = Router()
rag = RAGAnswerService()
matcher = ProductMatcher()


async def _answer_markdown(message: types.Message, text: str, **kwargs: object) -> None:
    try:
        await message.answer(to_telegram_html(text), parse_mode="HTML", **kwargs)
    except TelegramBadRequest:
        await message.answer(text, **kwargs)


def _cart_buttons(products: list[Product]) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=f"+ В корзину: {product.title}",
                callback_data=f"cart:add:{product.article}",
            )
        ]
        for product in products
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


@router.message()
async def ai_handler(message: types.Message, user: User) -> None:
    if not message.text:
        return
    await message.bot.send_chat_action(message.chat.id, action=ChatAction.TYPING)

    if matcher.is_product_query(message.text):
        matches = matcher.match(message.text)
        answer = (
            matcher.format(message.text)
            or "Не нашёл подходящих моделей. Уточните запрос или откройте /catalog."
        )
        products = [match.product for match in matches]
        await _answer_markdown(
            message, answer, reply_markup=_cart_buttons(products) if products else None
        )
        return

    history = dialog_memory.get(user.telegram_id)
    dialog_memory.add(user.telegram_id, "user", message.text)
    answer = await rag.generate(message.text, history)
    dialog_memory.add(user.telegram_id, "assistant", answer)
    products = matcher.find_references(answer) or matcher.find_references(message.text)
    await _answer_markdown(
        message, answer, reply_markup=_cart_buttons(products) if products else None
    )
