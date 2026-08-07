from types import SimpleNamespace
from unittest.mock import patch

from src.rag import vector_store as vs
from src.services.llm import LLMService


def test_embedding_cache_reuses_encode() -> None:
    vs._embed_cache.clear()
    fake = SimpleNamespace(
        tolist=lambda: [0.25, 0.5, 0.75],
        encode=lambda text: SimpleNamespace(tolist=lambda: [0.25, 0.5, 0.75]),
    )
    with patch.object(vs, "_model", fake):
        first = vs.get_embedding("какая заточка")
        second = vs.get_embedding("какая заточка")
        assert first == second == [0.25, 0.5, 0.75]


async def test_search_reuses_cache() -> None:
    vs._query_cache.clear()
    vs._embed_cache.clear()
    query = "сталь для охоты какая лучше"
    with patch.object(vs, "get_embedding", wraps=vs.get_embedding) as mocked:
        await vs.search(query, top_k=3)
        second = await vs.search(query, top_k=3)
        assert second is not None
        assert mocked.call_count == 1


async def test_llm_cache_bypasses_request() -> None:
    service = LLMService(cache_limit=10)
    service.cache["вопрос"] = "готовый ответ"
    with patch.object(service, "_request", return_value="другой ответ") as req:
        result = await service.generate("вопрос")
    req.assert_not_awaited()
    assert result == "готовый ответ"
