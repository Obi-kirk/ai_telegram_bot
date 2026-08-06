from aiogram import Router, types
from aiogram.enums import ChatAction

from src.services.rag_answers import RAGAnswerService

router = Router()
rag = RAGAnswerService()


@router.message()
async def ai_handler(message: types.Message) -> None:
    if not message.text:
        return
    await message.bot.send_chat_action(message.chat.id, action=ChatAction.TYPING)
    answer = await rag.generate(message.text)
    await message.answer(answer)
