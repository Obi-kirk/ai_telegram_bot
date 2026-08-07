from src.services.history import DialogMemory


def test_memory_add_get() -> None:
    memory = DialogMemory(limit=6)
    memory.add(1, "user", "Привет")
    memory.add(1, "assistant", "Здравствуйте")
    assert memory.get(1) == [("user", "Привет"), ("assistant", "Здравствуйте")]


def test_memory_limit() -> None:
    memory = DialogMemory(limit=2)
    for i in range(4):
        memory.add(1, "user", str(i))
    assert memory.get(1) == [("user", "2"), ("user", "3")]


def test_memory_isolated_per_user() -> None:
    memory = DialogMemory()
    memory.add(1, "user", "a")
    memory.add(2, "user", "b")
    assert memory.get(1) == [("user", "a")]
    assert memory.get(2) == [("user", "b")]


def test_memory_clear() -> None:
    memory = DialogMemory()
    memory.add(1, "user", "a")
    memory.clear(1)
    assert memory.get(1) == []
