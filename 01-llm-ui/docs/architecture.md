# Архитектура

## Обзор

```
┌─────────────────┐     HTTP POST      ┌─────────────────┐
│  Streamlit UI   │ ─────────────────► │   FastAPI       │
│  (ui/app.py)    │ ◄───────────────── │   /recommend    │
└─────────────────┘     JSON           └────────┬────────┘
                                                  │
                                         ┌────────▼────────┐
                                         │ Recommendation  │
                                         │ Service         │
                                         └────────┬────────┘
                                                  │
                              ┌───────────────────┼───────────────────┐
                              │                   │                   │
                     ┌────────▼────────┐ ┌────────▼────────┐ ┌───────▼───────┐
                     │ Prompt Builder  │ │  OpenAI Client  │ │ Response      │
                     │ (llm/prompts)   │ │  (llm/client)   │ │ Parser        │
                     └─────────────────┘ └─────────────────┘ │ (llm/parser)  │
                                                              └───────────────┘
```

## Слои и ответственность

### `api/` — транспортный слой

- Принимает HTTP-запросы, возвращает HTTP-ответы.
- Валидирует вход через Pydantic (`RecommendRequest`).
- Делегирует работу `RecommendationService`.
- Преобразует исключения в HTTP-коды (`422`, `502`, `500`).

**Не делает:** вызовов OpenAI, сборки промптов, бизнес-правил.

### `services/` — бизнес-логика

- Оркестрирует сценарий рекомендации.
- Собирает промпт, вызывает LLM, парсит и обогащает ответ.
- Может применять дополнительные правила (например, ограничение числа рекомендаций).

**Не делает:** работы с HTTP, чтения `.env` напрямую.

### `llm/` — интеграция с языковой моделью

| Модуль | Назначение |
|--------|------------|
| `client.py` | Инициализация OpenAI-клиента, вызов `chat.completions` с параметрами из config |
| `prompts.py` | System/user-промпты, подстановка переменных |
| `parser.py` | Извлечение JSON из ответа, маппинг в `RecommendResponse` |

### `config/` — конфигурация

- `Settings` на базе `pydantic-settings`.
- Читает `.env`: API-ключ, модель, температура, URL API.
- Единственная точка доступа к настройкам (`get_settings()` с кэшированием).

### `ui/` — Streamlit-интерфейс

- Форма ввода: модель телефона, сценарий использования, опциональные поля.
- HTTP-клиент (`httpx` / `requests`) к `POST /recommend`.
- Отображение результата: карточки рекомендаций или сообщение «обновление не требуется».

## Поток данных

1. Пользователь заполняет форму в Streamlit.
2. UI отправляет `RecommendRequest` на `POST /recommend`.
3. FastAPI валидирует тело запроса (Pydantic).
4. `RecommendationService.recommend()`:
   - строит промпт из шаблона;
   - вызывает OpenAI с `response_format: json_object`;
   - парсит JSON в `LLMRecommendationPayload`;
   - маппит в `RecommendResponse`.
5. API возвращает JSON клиенту.
6. Streamlit рендерит результат.

## Зависимости между модулями

```
config/settings.py
    ↑
llm/client.py, llm/prompts.py
    ↑
llm/parser.py
    ↑
services/recommendation.py
    ↑
api/endpoints/recommend.py
    ↑
main.py

ui/app.py  →  HTTP  →  main.py
```

Направление импортов — только вниз по цепочке. `llm/` не импортирует `api/` или `ui/`.

## Обработка ошибок

| Ситуация | Слой | HTTP-код |
|----------|------|----------|
| Невалидное тело запроса | FastAPI / Pydantic | `422` |
| Пустой или невалидный JSON от LLM | `llm/parser` | `502` |
| Таймаут / ошибка OpenAI API | `llm/client` | `502` |
| Неожиданная ошибка | `services/` | `500` |

## Переменные окружения (`.env`)

```env
# OpenAI
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
OPENAI_TEMPERATURE=0.3
OPENAI_TIMEOUT_SECONDS=30

# API
API_HOST=0.0.0.0
API_PORT=8000

# Streamlit → API
API_BASE_URL=http://localhost:8000
```

## Технологический стек

| Компонент | Библиотека |
|-----------|------------|
| API | FastAPI, Uvicorn |
| Валидация / настройки | Pydantic v2, pydantic-settings |
| LLM | openai (официальный SDK) |
| UI | Streamlit |
| HTTP-клиент (UI, тесты) | httpx |
| Тесты | pytest, pytest-asyncio, httpx |
