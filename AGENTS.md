# AGENTS.md — Telegram AI Agent (Минимализм)

## Проект
- **Путь**: `/home/obihiro/Proj/ai_bot_first`
- **Python**: 3.14.4 | **ОС**: Ubuntu 26.04
- **Библиотеки**: aiogram 3.x, SQLAlchemy async, asyncpg, python-dotenv
- **AI**: DeepSeek V4 Flash (бесплатно), позже OpenRouter / Groq
- **БД**: PostgreSQL (возможно с pgvector для RAG)

## Структура
src/
├── handlers/ # Команды бота
├── services/ # RAG, API, календарь
├── database/ # Модели SQLAlchemy
├── rag/ # Векторная БД, эмбеддинги
├── config/ # Настройки
└── utils/ # Логи, валидация
tests/
.env (НЕ КОММИТИТЬ!)
requirements.txt

text

## Команды
```bash
# Установка
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Запуск
python -m src.main

# Тесты
pytest tests/ -v

# Форматирование (black + isort)
black src/ tests/ && isort src/ tests/

# Линтинг (ruff)
ruff check src/ tests/
Стиль
black (88 символов), isort, ruff

Type hints обязательны

Имена: snake_case (файлы, функции, переменные), PascalCase (классы)

Все хендлеры — async def

.env (обязательно)
text
TELEGRAM_BOT_TOKEN=токен
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/db
OPENROUTER_API_KEY=ключ   # или GROQ / Google
БЕЗОПАСНОСТЬ (только критичное)
Секреты: НИКОГДА не выводи, не коммить .env.

Промпт-инъекции: Санитизируй пользовательский ввод перед LLM (удаляй "ignore previous", "system:").

Белый список доменов:

api.telegram.org

api.openrouter.ai | api.groq.com | generativelanguage.googleapis.com

Твой PostgreSQL (localhost)

Всё остальное — запрещено.

Подтверждение: Любое удаление/изменение данных — только после подтверждения пользователем.

Логи: Логируй действия, НЕ логируй секреты и PII.

PII: Сейчас только Telegram ID и имя. Никаких телефонов/email.

AGENTS.md — единственный источник правил. Не дублируй в других файлах.

Границы
Можно	Нельзя
Читать: src/, tests/, AGENTS.md	Читать: .env, config/secrets/
Писать: src/ (с обоснованием)	Писать: .env, конфиги с секретами
Запросы: только из белого списка	Любые другие домены
Изменять БД: только через SQLAlchemy	Прямые SQL-запросы, удаление без подтверждения
Экономия токенов и запросов
Промпты: Пиши кратко, без "пожалуйста" и "можешь ли ты". Используй конкретные инструкции.

История: Не храни длинные диалоги без необходимости. Очищай контекст, если задача завершена.

RAG: Оптимизируй чанки (размер 500–1000 токенов), используй релевантный поиск топ-3–5.

Кэширование: Кэшируй частые запросы (например, список товаров, FAQ).

Модели: Для простых задач используй более дешёвые модели (например, Groq Llama 3.1 8B), для сложных — DeepSeek / GPT.

Лимиты: Следи за использованием токенов в OpenRouter / Groq. Установи бюджет в коде (например, max_tokens=1000).

Обновляй этот файл по мере роста проекта. Меньше воды — больше пользы.