from src.rag.vector_store import search
from src.services.llm import LLMService

_INSTRUCTION = (
    "Ты — консультант магазина ножей «Кузница Северного Ветра».\n"
    "Отвечай на русском, опираясь на предоставленный контекст.\n"
    "Если в контексте нет точного ответа — честно скажи, что этой "
    "информации нет, и предложи уточнить вопрос.\n"
    "Не выдумывай цены, материалы и гарантии, которых нет в контексте.\n"
    "Отвечай структурированно и кратко (2–5 предложений).\n\n"
    "Контекст:\n{context}\n\nВопрос: {question}"
)


class RAGAnswerService:
    """Строит ответ: векторный поиск → контекст → LLM."""

    def __init__(self, llm: LLMService | None = None) -> None:
        self.llm = llm or LLMService()

    async def generate(self, question: str) -> str:
        docs = await search(question)
        if not docs:
            return await self.llm.generate(question)

        context = "\n\n".join(doc.text for doc in docs)
        prompt = _INSTRUCTION.format(context=context, question=question)
        return await self.llm.generate(prompt)
