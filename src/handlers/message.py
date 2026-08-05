from aiogram import Router, types
from aiogram.enums import ChatAction

from src.services.llm import LLMService

router = Router()
llm = LLMService()


@router.message()
async def ai_handler(message: types.Message) -> None:
    if not message.text:
        return
    await message.bot.send_chat_action(message.chat.id, action=ChatAction.TYPING)
    answer = await llm.generate(message.text)
    await message.answer(answer)
