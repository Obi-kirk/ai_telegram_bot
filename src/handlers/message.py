from aiogram import Router, types
from aiogram.enums import ChatAction

from src.database.models import User
from src.services.history import dialog_memory
from src.services.matcher import ProductMatcher
from src.services.rag_answers import RAGAnswerService

router = Router()
rag = RAGAnswerService()
matcher = ProductMatcher()


@router.message()
async def ai_handler(message: types.Message, user: User) -> None:
    if not message.text:
        return
    await message.bot.send_chat_action(message.chat.id, action=ChatAction.TYPING)

    if matcher.is_product_query(message.text):
        answer = (
            matcher.format(message.text)
            or "Не нашёл подходящих моделей. Уточните запрос или откройте /catalog."
        )
        await message.answer(answer)
        return

    history = dialog_memory.get(user.telegram_id)
    dialog_memory.add(user.telegram_id, "user", message.text)
    answer = await rag.generate(message.text, history)
    dialog_memory.add(user.telegram_id, "assistant", answer)
    await message.answer(answer)
