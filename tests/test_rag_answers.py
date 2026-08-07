from unittest.mock import AsyncMock, patch

from src.database.models import Document
from src.services.rag_answers import RAGAnswerService


def _doc(source: str, text: str = "Контекст") -> Document:
    return Document(id=1, text=text, source=source, embedding=[0.0] * 384)


async def test_generate_with_docs_uses_context() -> None:
    llm = AsyncMock(spec=["generate"])
    llm.generate = AsyncMock(return_value="Возврат — 14 дней.")
    service = RAGAnswerService(llm=llm)
    docs = [_doc("policy.txt"), _doc("faq.txt"), _doc("policy.txt")]

    with patch("src.services.rag_answers.search", new=AsyncMock(return_value=docs)):
        result = await service.generate("срок возврата?")

    assert result == "Возврат — 14 дней."
    assert "Источник" not in result
    assert llm.generate.await_args.args[0].startswith("Ты — ассистент")


async def test_generate_without_docs_plain_llm() -> None:
    llm = AsyncMock(spec=["generate"])
    llm.generate = AsyncMock(return_value="Не знаю.")
    service = RAGAnswerService(llm=llm)

    with patch("src.services.rag_answers.search", new=AsyncMock(return_value=[])):
        result = await service.generate("вопрос")

    assert result == "Не знаю."
