import asyncio
import os

from sentence_transformers import SentenceTransformer
from sqlalchemy import select

from src.database.db import session_factory
from src.database.models import Document

CHUNK_SIZE = 400
CHUNK_OVERLAP = 50
TOP_K = 5
RELEVANCE_THRESHOLD = 0.7

_model = SentenceTransformer("all-MiniLM-L6-v2")


def get_embedding(text: str) -> list[float]:
    return _model.encode(text).tolist()


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
        return list(result.scalars().all())


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
