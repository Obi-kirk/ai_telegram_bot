from src.rag.vector_store import search
from src.services.llm import LLMService

_INSTRUCTION = (
    "Ты — консультант магазина ножей «Кузница Северного Ветра».\n"
    "Отвечай на русском, опираясь на предоставленный контекст и историю диалога.\n"
    "Если в контексте нет точного ответа — честно скажи, что этой "
    "информации нет, и предложи уточнить вопрос.\n"
    "Не выдумывай цены, материалы и гарантии, которых нет в контексте.\n"
    "Отвечай структурированно и кратко (2–5 предложений).\n"
    "История диалога:\n{history}\n\n"
    "Контекст:\n{context}\n\nВопрос: {question}"
)

_ROLE_LABELS = {"user": "Пользователь", "assistant": "Консультант"}


def _format_history(history: list[tuple[str, str]] | None) -> str:
    if not history:
        return "—"
    lines = [f"{_ROLE_LABELS.get(role, role)}: {text}" for role, text in history]
    return "\n".join(lines)


class RAGAnswerService:
    """Строит ответ: векторный поиск + история диалога → контекст → LLM."""

    def __init__(self, llm: LLMService | None = None) -> None:
        self.llm = llm or LLMService()

    async def generate(
        self,
        question: str,
        history: list[tuple[str, str]] | None = None,
    ) -> str:
        docs = await search(question)
        context = "\n\n".join(doc.text for doc in docs)
        if not context and not history:
            return await self.llm.generate(question)

        prompt = _INSTRUCTION.format(
            history=_format_history(history),
            context=context or "нет контекста",
            question=question,
        )
        return await self.llm.generate(prompt)
