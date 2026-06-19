# Архитектура

## Обзор системы

```mermaid
flowchart TB
    subgraph Client["Клиент"]
        UI["Streamlit UI<br/>streamlit_app.py"]
    end

    subgraph API["Транспортный слой — FastAPI"]
        REC["/recommendation"]
        HIST["/history"]
        PROF["/profile"]
        FB["/feedback"]
        HC["/health"]
    end

    subgraph Services["Бизнес-логика"]
        RS["RecommendationService"]
        PS["ProfileService"]
        FS["FeedbackService"]
        PB["PromptBuilderService"]
    end

    subgraph LLM["Слой LLM"]
        BP["BaseLLMProvider"]
        OAI["OpenAIProvider"]
        PR["prompts.py"]
        SCH["schemas.py"]
    end

    subgraph Storage["Хранилище"]
        DB[("SQLite<br/>app.db")]
    end

    UI -->|HTTP JSON| API
    REC --> RS
    HIST --> RS
    PROF --> PS
    FB --> FS
    RS --> PB
    RS --> BP
    PB --> PR
    BP --> OAI
    OAI -->|OpenAI API| EXT["OpenAI"]
    RS --> DB
    PS --> DB
    FS --> DB
```

## Слои и ответственность

### `api/` — транспортный слой

- Приём HTTP-запросов, возврат HTTP-ответов.
- Валидация входа через Pydantic.
- Делегирование сервисам.
- Преобразование доменных исключений в HTTP-коды.

**Не делает:** вызовов OpenAI, сборки промптов, прямых SQL-запросов (кроме DI сессии БД).

### `services/` — бизнес-логика

| Сервис | Задачи |
|--------|--------|
| `RecommendationService` | Анализ запроса, оркестрация уточнений, вызов LLM, сохранение истории |
| `PromptBuilderService` | Сборка system/user-промптов из шаблонов и контекста |
| `ProfileService` | CRUD профиля пользователя (бюджет, активность, предпочтения) |
| `FeedbackService` | Сохранение оценок и комментариев к рекомендациям |

**Не делает:** работы с HTTP, чтения `.env` напрямую, импорта FastAPI.

### `llm/` — интеграция с языковой моделью

| Модуль | Назначение |
|--------|------------|
| `base_provider.py` | Абстрактный интерфейс `generate()` / `generate_json()` |
| `openai_provider.py` | Реализация через OpenAI SDK |
| `prompts.py` | `SYSTEM_PROMPT`, `CLARIFICATION_PROMPT`, `RECOMMENDATION_PROMPT` |
| `schemas.py` | Pydantic-схемы ответов LLM (`ClarificationPayload`, `RecommendationPayload`) |

### `config/` — конфигурация

- `settings.py` — `pydantic-settings`, переменные из `.env`.
- `database.py` — engine, session factory, инициализация таблиц.
- `logging.py` — уровни INFO / WARNING / ERROR.

### `streamlit_app.py` — интерфейс

- Многошаговая форма: запрос → уточнения → результат.
- HTTP-клиент (`httpx`) к FastAPI.
- Страницы/секции: новая рекомендация, история, профиль, обратная связь.

## Диаграмма компонентов

```mermaid
C4Context
    title Контекст системы — Сервис рекомендаций досуга

    Person(user, "Пользователь", "Ищет идеи для досуга")
    System(app, "Leisure Recommendation App", "FastAPI + Streamlit + SQLite")
    System_Ext(openai, "OpenAI API", "Генерация уточнений и рекомендаций")

    Rel(user, app, "Вводит запрос, отвечает на вопросы, оценивает результат")
    Rel(app, openai, "Chat Completions / Structured Output")
```

## Sequence: получение рекомендации

```mermaid
sequenceDiagram
    actor User as Пользователь
    participant UI as Streamlit
    participant API as FastAPI
    participant RS as RecommendationService
    participant PB as PromptBuilder
    participant LLM as OpenAIProvider
    participant DB as SQLite

    User->>UI: Вводит запрос о досуге
    UI->>API: POST /recommendation
    API->>RS: start_recommendation(query, profile_id?)

    RS->>DB: Создать сессию (status=collecting_context)
    RS->>PB: build_clarification_prompt(query, profile)
    PB-->>RS: prompt
    RS->>LLM: generate_json(prompt)
    LLM-->>RS: ClarificationPayload

    alt Достаточно контекста
        RS->>PB: build_recommendation_prompt(...)
        RS->>LLM: generate_json(prompt)
        LLM-->>RS: RecommendationPayload
        RS->>DB: Сохранить recommendation, закрыть сессию
        RS-->>API: RecommendationResponse
        API-->>UI: 200 + рекомендация
        UI-->>User: Показать результат
    else Нужны уточнения
        RS->>DB: Обновить сессию (questions)
        RS-->>API: ClarificationResponse
        API-->>UI: 200 + вопросы + session_id
        UI-->>User: Форма с вопросами

        User->>UI: Отвечает на вопросы
        UI->>API: POST /recommendation/continue
        API->>RS: continue_recommendation(session_id, answers)
        RS->>DB: Дополнить context
        RS->>PB: build_recommendation_prompt(...)
        RS->>LLM: generate_json(prompt)
        LLM-->>RS: RecommendationPayload
        RS->>DB: Сохранить recommendation
        RS-->>API: RecommendationResponse
        API-->>UI: 200 + рекомендация
        UI-->>User: Показать результат
    end
```

## Sequence: обратная связь

```mermaid
sequenceDiagram
    actor User as Пользователь
    participant UI as Streamlit
    participant API as FastAPI
    participant FS as FeedbackService
    participant DB as SQLite

    User->>UI: Ставит оценку и комментарий
    UI->>API: POST /feedback
    API->>FS: create_feedback(recommendation_id, rating, comment)
    FS->>DB: Проверить recommendation_id
    FS->>DB: INSERT feedback
    FS-->>API: FeedbackResponse
    API-->>UI: 201 Created
    UI-->>User: Подтверждение
```

## ER-диаграмма SQLite

```mermaid
erDiagram
    user_profile ||--o{ recommendation_sessions : "использует"
    recommendation_sessions ||--o| recommendations : "завершается в"
    recommendations ||--o{ feedback : "получает"

    user_profile {
        int id PK
        text budget
        text activity_level
        text favorite_activities
        text disliked_activities
        datetime created_at
        datetime updated_at
    }

    recommendation_sessions {
        int id PK
        int profile_id FK "nullable"
        text user_query
        text context "JSON"
        text status "enum"
        text pending_questions "JSON nullable"
        datetime created_at
        datetime updated_at
    }

    recommendations {
        int id PK
        int session_id FK
        text user_query
        text context "JSON"
        text recommendation "JSON"
        datetime created_at
    }

    feedback {
        int id PK
        int recommendation_id FK
        int rating
        text comment "nullable"
        datetime created_at
    }

    app_settings {
        text key PK
        text value
        datetime updated_at
    }
```

> Таблица `recommendation_sessions` добавлена для многошагового сценария (уточняющие вопросы). В исходном ТЗ контекст хранился только в `recommendations`; для MVP сессия — промежуточное состояние до финального ответа.

## State machine сессии рекомендации

```mermaid
stateDiagram-v2
    [*] --> collecting_context: POST /recommendation

    collecting_context --> awaiting_answers: LLM вернул вопросы
    collecting_context --> completed: контекста достаточно сразу

    awaiting_answers --> completed: POST /continue + финальный LLM-ответ
    awaiting_answers --> failed: ошибка LLM / таймаут

    completed --> [*]
    failed --> [*]
```

## Зависимости между модулями

```mermaid
flowchart BT
    settings["config/settings.py"]
    database["config/database.py"]
    logging["config/logging.py"]

    base["llm/base_provider.py"]
    openai["llm/openai_provider.py"]
    prompts["llm/prompts.py"]
    llm_schemas["llm/schemas.py"]

    prompt_builder["services/prompt_builder_service.py"]
    rec_svc["services/recommendation_service.py"]
    prof_svc["services/profile_service.py"]
    fb_svc["services/feedback_service.py"]

    api_rec["api/recommendations.py"]
    api_prof["api/profile.py"]
    api_fb["api/feedback.py"]
    api_hc["api/healthcheck.py"]

    main["main.py"]
    ui["streamlit_app.py"]

    settings --> database
    settings --> openai
    settings --> logging

    base --> openai
    prompts --> prompt_builder
    llm_schemas --> rec_svc
    openai --> rec_svc
    prompt_builder --> rec_svc
    database --> rec_svc
    database --> prof_svc
    database --> fb_svc

    rec_svc --> api_rec
    prof_svc --> api_prof
    fb_svc --> api_fb

    api_rec --> main
    api_prof --> main
    api_fb --> main
    api_hc --> main

    main -.->|HTTP| ui
```

Направление импортов — только вниз по цепочке. `llm/` не импортирует `api/` или `streamlit_app.py`.

## Обработка ошибок

| Ситуация | Слой | HTTP-код |
|----------|------|----------|
| Невалидное тело запроса | FastAPI / Pydantic | `422` |
| Сессия не найдена / истекла | `RecommendationService` | `404` |
| Рекомендация не найдена (feedback) | `FeedbackService` | `404` |
| Невалидный JSON от LLM | `llm/openai_provider` | `502` |
| Таймаут / ошибка OpenAI API | `llm/openai_provider` | `502` |
| Нарушение бизнес-правил (дубль feedback) | `FeedbackService` | `409` |
| Неожиданная ошибка | любой | `500` |

## Переменные окружения

```env
# OpenAI
OPENAI_API_KEY=sk-...
MODEL_NAME=gpt-4o-mini
OPENAI_TIMEOUT_SECONDS=60

# База данных
DATABASE_URL=sqlite:///./app.db

# API
API_HOST=0.0.0.0
API_PORT=8000

# Streamlit → API
API_BASE_URL=http://localhost:8000

# Лимиты
MAX_USER_QUERY_LENGTH=1000
MAX_CLARIFICATION_ROUNDS=2
SESSION_TTL_HOURS=24
```

## Технологический стек

| Компонент | Библиотека |
|-----------|------------|
| API | FastAPI, Uvicorn |
| Валидация / настройки | Pydantic v2, pydantic-settings |
| ORM (опционально) | SQLAlchemy 2.x |
| LLM | openai (официальный SDK) |
| UI | Streamlit |
| HTTP-клиент (UI, тесты) | httpx |
| Тесты | pytest, pytest-asyncio |

## Исключённые технологии (MVP)

Redis, PostgreSQL, Docker, Kubernetes, Prometheus, Grafana — не используются на этапе MVP для снижения сложности инфраструктуры.
