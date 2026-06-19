# Рекомендательный сервис смартфонов

Сервис на базе **FastAPI** и **OpenAI**, который анализирует текущую модель телефона и сценарий использования, после чего рекомендует модели для обновления или сообщает, что обновление не требуется.

Интерфейс — **Streamlit**. Бэкенд — REST API с единственным публичным эндпоинтом `POST /recommend`.

## Содержание документации

| Документ | Описание |
|----------|----------|
| [architecture.md](./architecture.md) | Архитектура, структура каталогов, поток данных |
| [models.md](./models.md) | Pydantic-модели, enum-типы, валидация |
| [api.md](./api.md) | Контракт API, коды ответов, примеры |
| [prompts.md](./prompts.md) | Шаблоны промптов и парсинг ответа LLM |
| [development-plan.md](./development-plan.md) | Пошаговый план построения проекта |
| [streamlit-ui.md](./streamlit-ui.md) | Спецификация Streamlit-интерфейса |
| [testing.md](./testing.md) | Стратегия unit- и интеграционных тестов |

## Быстрый старт (после реализации)

```bash
# 1. Установка зависимостей
cd 01-llm-ui
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. Настройка окружения
cp .env.example .env
# Заполнить OPENAI_API_KEY

# 3. Запуск API
uvicorn main:app --reload --port 8000

# 4. Запуск UI (в отдельном терминале)
streamlit run ui/app.py
```

## Целевая структура проекта

```
01-llm-ui/
├── .env                    # Секреты и переменные окружения (не в git)
├── .env.example            # Шаблон переменных окружения
├── main.py                 # Точка входа FastAPI
├── requirements.txt
├── api/
│   ├── __init__.py
│   ├── router.py           # Регистрация маршрутов
│   └── endpoints/
│       ├── __init__.py
│       └── recommend.py    # POST /recommend
├── services/
│   ├── __init__.py
│   └── recommendation.py   # Оркестрация: валидация → LLM → ответ
├── llm/
│   ├── __init__.py
│   ├── client.py           # Обёртка над OpenAI SDK
│   ├── prompts.py          # Шаблоны промптов
│   └── parser.py           # Парсинг структурированного ответа LLM
├── config/
│   ├── __init__.py
│   └── settings.py         # Pydantic Settings из .env
├── ui/
│   └── app.py              # Streamlit-интерфейс
├── tests/
│   ├── conftest.py
│   ├── unit/
│   │   ├── test_models.py
│   │   ├── test_prompts.py
│   │   └── test_parser.py
│   └── integration/
│       ├── test_recommend_api.py
│       └── test_recommendation_service.py
└── docs/                   # Эта документация
```

## Ключевые решения

- **Один эндпоинт** — минимальный публичный контракт, вся логика за ним.
- **Structured output** — LLM возвращает JSON по схеме; парсер валидирует через Pydantic.
- **Разделение слоёв** — API не знает о деталях OpenAI; сервис не знает о HTTP.
- **Streamlit как клиент** — UI вызывает API, не импортирует бизнес-логику напрямую.
