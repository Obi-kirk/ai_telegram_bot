import asyncio
import os
from collections import OrderedDict

from sentence_transformers import SentenceTransformer
from sqlalchemy import select

from src.database.db import session_factory
from src.database.models import Document

CHUNK_SIZE = 400
CHUNK_OVERLAP = 50
TOP_K = 5
RELEVANCE_THRESHOLD = 0.8
_EMBED_CACHE_LIMIT = 512
_QUERY_CACHE_LIMIT = 256

_model = SentenceTransformer("all-MiniLM-L6-v2")
_embed_cache: OrderedDict[str, list[float]] = OrderedDict()
_query_cache: OrderedDict[tuple[str, int], list[Document]] = OrderedDict()


def get_embedding(text: str) -> list[float]:
    cached = _embed_cache.get(text)
    if cached is not None:
        _embed_cache.move_to_end(text)
        return cached
    vector = _model.encode(text).tolist()
    _embed_cache[text] = vector
    if len(_embed_cache) > _EMBED_CACHE_LIMIT:
        _embed_cache.popitem(last=False)
    return vector


def chunk_text(
    text: str,
    chunk_size: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP,
) -> list[str]:
    words = text.split()
    step = chunk_size - overlap
    return [
        " ".join(words[i : i + chunk_size])
        for i in range(0, len(words), step)
        if words[i : i + chunk_size]
    ]


async def save_chunk(text: str, source: str = "data") -> None:
    doc = Document(text=text, source=source, embedding=get_embedding(text))
    async with session_factory() as session:
        session.add(doc)
        await session.commit()


async def search(query: str, top_k: int = TOP_K) -> list[Document]:
    """Возвращает релевантные чанки (косинусное расстояние ниже порога)."""
    key = (query, top_k)
    cached = _query_cache.get(key)
    if cached is not None:
        _query_cache.move_to_end(key)
        return cached

    q_emb = get_embedding(query)
    distance = Document.embedding.cosine_distance(q_emb)
    stmt = (
        select(Document)
        .where(distance < RELEVANCE_THRESHOLD)
        .order_by(distance)
        .limit(top_k)
    )
    async with session_factory() as session:
        result = await session.execute(stmt)
        docs = list(result.scalars().all())

    _query_cache[key] = docs
    if len(_query_cache) > _QUERY_CACHE_LIMIT:
        _query_cache.popitem(last=False)
    return docs


def _read_file(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


async def index_documents(folder_path: str) -> int:
    """Индексирует все .txt файлы из папки в векторную БД. Запускать вручную."""
    count = 0
    for filename in os.listdir(folder_path):
        if not filename.endswith(".txt"):
            continue
        path = os.path.join(folder_path, filename)
        text = await asyncio.to_thread(_read_file, path)
        for chunk in chunk_text(text):
            await save_chunk(chunk, source=filename)
            count += 1
    return count
