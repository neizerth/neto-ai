# Сервис рекомендаций досуга (LLM Wasting Time)

MVP-сервис на базе **FastAPI**, **OpenAI** и **SQLite**, который помогает пользователю выбрать, как провести свободное время. Сервис уточняет контекст через диалог с LLM и возвращает персональную рекомендацию с альтернативами.

Интерфейс — **Streamlit**. Бэкенд — REST API. Персистентность — **SQLite**.

## Содержание документации

| Документ | Описание |
|----------|----------|
| [architecture.md](./architecture.md) | Архитектура, Mermaid-диаграммы, потоки данных |
| [models.md](./models.md) | Pydantic-модели, ORM-схема SQLite, enum-типы |
| [validation.md](./validation.md) | Ограничения полей, правила валидации, согласованность данных |
| [api.md](./api.md) | Контракт REST API, коды ответов, примеры |
| [streamlit-ui.md](./streamlit-ui.md) | Спецификация Streamlit-интерфейса |
| [task.md](./task.md) | Исходное техническое задание |

## Быстрый старт (после реализации)

```bash
# 1. Установка зависимостей
cd 02-llm-wasting-time
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. Настройка окружения
cp .env.example .env
# Заполнить OPENAI_API_KEY

# 3. Запуск API
uvicorn main:app --reload --port 8000

# 4. Запуск UI (в отдельном терминале)
API_BASE_URL=http://localhost:8000 streamlit run streamlit_app.py
```

## Целевая структура проекта

```
02-llm-wasting-time/
├── .env                    # Секреты и переменные окружения (не в git)
├── .env.example            # Шаблон переменных окружения
├── main.py                 # Точка входа FastAPI
├── streamlit_app.py        # Streamlit-интерфейс
├── requirements.txt
├── api/
│   ├── recommendations.py  # POST /recommendation, POST /recommendation/continue
│   ├── profile.py          # GET/PUT /profile
│   ├── feedback.py         # POST /feedback
│   └── healthcheck.py      # GET /health
├── services/
│   ├── recommendation_service.py
│   ├── profile_service.py
│   ├── feedback_service.py
│   └── prompt_builder_service.py
├── llm/
│   ├── base_provider.py    # Абстрактный провайдер LLM
│   ├── openai_provider.py  # Реализация OpenAI
│   ├── prompts.py          # Системные промпты
│   └── schemas.py          # Схемы ответов LLM
├── config/
│   ├── settings.py
│   ├── database.py
│   └── logging.py
├── db/
│   └── models.py           # SQLAlchemy / raw SQL модели таблиц
├── tests/
│   ├── unit/
│   └── integration/
└── docs/                   # Эта документация
```

## Ключевые решения

- **Многошаговый сценарий** — при недостатке контекста LLM задаёт уточняющие вопросы; сессия хранится в SQLite до получения финальной рекомендации.
- **Слой LLM изолирован** — `BaseLLMProvider` позволяет заменить OpenAI без изменения сервисов.
- **Structured output** — финальный ответ LLM валидируется через Pydantic (`RecommendationPayload`).
- **Streamlit как клиент** — UI вызывает API по HTTP, не импортирует бизнес-логику.
- **SQLite для MVP** — профили, история, обратная связь и настройки в одной БД без внешней инфраструктуры.

## Пользовательский сценарий (MVP)

1. Пользователь открывает Streamlit-интерфейс.
2. Описывает ситуацию («Не знаю, как провести субботу»).
3. При необходимости отвечает на уточняющие вопросы AI.
4. Получает персональную рекомендацию с альтернативами, оценкой бюджета и времени.
5. Просматривает историю прошлых рекомендаций.
6. Оценивает качество предложенного варианта (рейтинг + комментарий).
