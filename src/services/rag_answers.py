from src.database.models import Document
from src.rag.vector_store import search
from src.services.llm import LLMService

_INSTRUCTION = (
    "Ты — ассистент магазина «Кузница Северного Ветра». "
    "Отвечай на русском, опираясь ТОЛЬКО на предоставленный контекст. "
    "Если в контексте нет ответа — так и скажи, не выдумывай. "
    "Отвечай кратко и по делу.\n\n"
    "Контекст:\n{context}\n\nВопрос: {question}"
)


class RAGAnswerService:
    """Строит ответ: векторный поиск → контекст → LLM → ответ с источниками."""

    def __init__(self, llm: LLMService | None = None) -> None:
        self.llm = llm or LLMService()

    async def generate(self, question: str) -> str:
        docs = await search(question)
        if not docs:
            return await self.llm.generate(question)

        context = "\n\n".join(doc.text for doc in docs)
        prompt = _INSTRUCTION.format(context=context, question=question)
        answer = await self.llm.generate(prompt)
        return f"{answer}\n\nИсточники: {self._sources(docs)}"

    @staticmethod
    def _sources(docs: list[Document]) -> str:
        names = [doc.source for doc in docs if doc.source]
        unique = list(dict.fromkeys(names))
        return ", ".join(unique) if unique else "внутренняя база знаний"
