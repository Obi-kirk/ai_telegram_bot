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

## Роли и разграничение доступа

Три роли (столбец `users.role`, значения — строки):

| Роль | Доступ |
|---|---|
| user | Каталог, поиск, корзина (клиентские функции) |
| employee | Внутренние отчёты, заказы, статистика |
| admin | Всё, включая управление ролями и блокировку |

Статусы: `active` / `blocked` (заблокированный пользователь полностью игнорируется middleware).

Как это работает:

- `UserMiddleware` (src/handlers/access.py) — на каждый апдейт находит или создаёт пользователя в БД и кладёт его в `data["user"]`. Заблокированных — отбрасывает.
- `require_role(Role.EMPLOYEE, ...)` — декоратор хендлера: не подходящая роль → ответ "Нет доступа". Все внутренние команды обязаны иметь декоратор.
- Команды: `/setrole <id|@username> <user|employee|admin>`, `/block <id|@username>`, `/unblock <id|@username>`, `/admin_stats` (admin), `/employee_report` (employee+).
- Бутстрап админа: `ADMIN_IDS` в .env (через запятую) — эти ID получают роль admin при первом контакте с ботом.
- Нельзя менять роль/блокировать самого себя.
- Вебхук (будущее): проверять заголовок `X-Telegram-Bot-Api-Secret-Token` на сервере вебхука, чтобы отвергать запросы не от Telegram.

Правило: любой новый хендлер с внутренними данными обязан иметь `require_role` и проходить через `UserMiddleware`. Валидация входящих аргументов — через src/utils/sanitize.py (parse_role, parse_user_target).

Границы
Можно	Нельзя
Читать: src/, tests/, AGENTS.md	Читать: .env, config/secrets/
Писать: src/ (с обоснованием)	Писать: .env, конфиги с секретами
Запросы: только из белого списка	Любые другие домены
Изменять БД: только через SQLAlchemy	Прямые SQL-запросы, удаление без подтверждения
## Текущее состояние проекта (2026-08-07)

Сделано:
- Бот на polling запускается (`python -m src.main`), отвечает на /start и любые сообщения (LLM через OpenRouter DeepSeek, fallback Groq).
- RAG подключён к боту: RAGAnswerService (src/services/rag_answers.py) — поиск топ-5 косинусной близостью с порогом релевантности (RELEVANCE_THRESHOLD=0.8, нерелевантное → обычный LLM) → контекст + история диалога → LLM. Память диалога: src/services/history.py (DialogMemory, 6 последних сообщений на пользователя, в памяти процесса). Кэш: эмбеддинги и search (LRU в vector_store.py), LLM-кэш 200. Модель all-MiniLM-L6-v2 (384), 11 файлов из data/, 13 чанков, чанк 400/50, у чанков есть поле source (имя файла). Сноска с источниками в ответе отсутствует (убрана по запросу).
- Система ролей: UserMiddleware + require_role, команды /setrole, /block, /unblock, /admin_stats (сейчас показывает список пользователей с ID), /employee_report. Бутстрап: ADMIN_IDS в .env.
- Магазин: /catalog (парсинг data/catalog.txt → 8 товаров по категориям, под каждым товаром инлайн-кнопка «+» для добавления в корзину, CatalogService), /cart (add <артикул> [кол-во], clear, checkout; инлайн-кнопки +/−, оформление с подтверждением — без адресов и оплаты, тестовый проект), /status (заказы, статусы pending→Сборка и т.д.), /help. Reply-кнопки главного меню (Каталог/Корзина/Заказы/Помощь) — на /start и /help. Таблицы cart_items, orders.
- Поиск товара по описанию: ProductMatcher (src/services/matcher.py) — парсит бюджет/категорию/сталь/рукоять (детерминированный скоринг), отвечает списком моделей; кнопки «+ В корзину» под ответами (matcher-запросы и упоминание артикула/названия через find_references).
- Заказы: /order <id> <статус> (employee) — смена статуса заказа, /orders (employee) — список всех заказов (OrderService.get/set_status/list_all).
- Тесты: 50 шт (tests/) — роли, валидация, sanitize, RAGAnswerService, история диалога, кэш, каталог/корзина/заказы, матчер; используют реальную БД ai_bot, чистят свои данные, TESTING=1 включает NullPool.
- Инфраструктура: PostgreSQL 18 + pgvector 0.8.6, БД ai_bot, роль ai_bot (пароль только в .env). venv в .venv. Ремоут GitHub: Obi-kirk/ai_telegram_bot (ветка main). Коммиты от имени Obi-kirk.
- Идентификатор для admin_stats: telegram_id. Узнать свой ID — @userinfobot.

Отложено/планы:
- Вебхук с проверкой X-Telegram-Bot-Api-Secret-Token (сейчас polling; нужен VPS).
- Не логировать PII; .env никогда не коммитить (в .gitignore).
- systemd-автозапуск бота / Docker (сейчас запускается вручную через setsid).
- Улучшить сегментацию RAG по релевантности (порог 0.8 частично пропускает нерелевантное).

Перезапуск бота (после правок): `kill <pid> && cd ~/Proj/ai_bot_first && setsid nohup .venv/bin/python -m src.main > /tmp/bot.log 2>&1 < /dev/null &`

Экономия токенов и запросов
Промпты: Пиши кратко, без "пожалуйста" и "можешь ли ты". Используй конкретные инструкции.

История: Не храни длинные диалоги без необходимости. Очищай контекст, если задача завершена.

RAG: Оптимизируй чанки (размер 500–1000 токенов), используй релевантный поиск топ-3–5.

Кэширование: Кэшируй частые запросы (например, список товаров, FAQ).

Модели: Для простых задач используй более дешёвые модели (например, Groq Llama 3.1 8B), для сложных — DeepSeek / GPT.

Лимиты: Следи за использованием токенов в OpenRouter / Groq. Установи бюджет в коде (например, max_tokens=1000).

Обновляй этот файл по мере роста проекта. Меньше воды — больше пользы.