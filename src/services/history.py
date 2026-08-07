from collections import deque


class DialogMemory:
    """Хранит короткую историю диалога на пользователя (в памяти процесса)."""

    def __init__(self, limit: int = 6) -> None:
        self._limit = limit
        self._store: dict[int, deque[tuple[str, str]]] = {}

    def add(self, telegram_id: int, role: str, text: str) -> None:
        messages = self._store.setdefault(telegram_id, deque(maxlen=self._limit))
        messages.append((role, text))

    def get(self, telegram_id: int) -> list[tuple[str, str]]:
        return list(self._store.get(telegram_id, ()))

    def clear(self, telegram_id: int) -> None:
        self._store.pop(telegram_id, None)


dialog_memory = DialogMemory()
