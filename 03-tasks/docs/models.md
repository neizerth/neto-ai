# Модели данных

Все модели определены в `api/schemas.py` на базе **Pydantic v2** (`BaseModel`). Отдельного слоя ORM или доменных сущностей нет — `TaskResponse` используется и как DTO ответа API, и как объект внутри хранилища.

## Диаграмма связей

```
TaskCreate          TaskResponse
(request DTO)       (response / storage model)
─────────────       ──────────────────────────
title        ───►   id            (генерируется сервисом)
description  ───►   title
priority     ───►   description
                    priority
                    created_at    (генерируется сервисом)

TaskNotFoundDetail  (только для ошибки 404)
──────────────────
detail
task_id
```

## TaskCreate — входной DTO

Используется в теле запроса `POST /tasks`.

| Поле | Тип | Обязательное | Ограничения | Описание |
|------|-----|--------------|-------------|----------|
| `title` | `str` | да | 3–100 символов | Название задачи |
| `description` | `str \| None` | нет | — | Описание (по умолчанию `null`) |
| `priority` | `int` | да | 1–5 | Приоритет: 1 — низкий, 5 — высокий |

### Пример валидного JSON

```json
{
  "title": "Настроить CI/CD",
  "description": "Добавить GitHub Actions для автотестов",
  "priority": 3
}
```

Минимальный валидный запрос (без описания):

```json
{
  "title": "Test task",
  "priority": 3
}
```

### Ошибки валидации (422)

FastAPI возвращает `422 Unprocessable Entity`, если:

| Нарушение | Пример |
|-----------|--------|
| `title` короче 3 символов | `"ab"` |
| `title` длиннее 100 символов | строка из 101+ символов |
| `priority` вне диапазона 1–5 | `0`, `6`, `-1` |
| отсутствует обязательное поле | нет `title` или `priority` |
| неверный тип | `"priority": "high"` |

Формат ответа — стандартный Pydantic/FastAPI `detail` со списком ошибок по полям.

## TaskResponse — ответ API и модель хранения

Возвращается при успешном `POST /tasks`, `GET /tasks`, `GET /tasks/{task_id}`.

| Поле | Тип | Источник | Описание |
|------|-----|----------|----------|
| `id` | `int` | `InMemoryStorage.next_id()` | Уникальный идентификатор (автоинкремент с 1) |
| `title` | `str` | из `TaskCreate` | 3–100 символов |
| `description` | `str \| None` | из `TaskCreate` | Может быть `null` |
| `priority` | `int` | из `TaskCreate` | 1–5 |
| `created_at` | `datetime` | `datetime.now(timezone.utc)` | Время создания в UTC, ISO 8601 в JSON |

### Пример ответа

```json
{
  "id": 1,
  "title": "Настроить CI/CD",
  "description": "Добавить GitHub Actions для автотестов",
  "priority": 3,
  "created_at": "2026-06-23T12:00:00.123456+00:00"
}
```

Поля `id` и `created_at` клиент **не передаёт** — они назначаются на сервере в `TaskService.create_task`.

### Сериализация datetime

Pydantic v2 сериализует `datetime` в ISO 8601. Точный формат дробной части секунд зависит от микросекунд момента создания.

## TaskNotFoundDetail — схема ошибки 404

Используется в `responses={404: {"model": TaskNotFoundDetail}}` для документации OpenAPI и как структура `detail` при `HTTPException`.

| Поле | Тип | По умолчанию | Описание |
|------|-----|--------------|----------|
| `detail` | `str` | `"Task not found"` | Текстовое сообщение |
| `task_id` | `int` | — | ID, по которому задача не найдена |

### Пример ответа 404

```json
{
  "detail": {
    "detail": "Task not found",
    "task_id": 999
  }
}
```

> **Замечание:** из-за особенностей FastAPI `HTTPException(detail=...)` поле `detail` в корне JSON оборачивает объект `TaskNotFoundDetail`. Это отражено в интеграционном тесте `test_get_task_not_found`.

## Маппинг слоёв

| Слой | Модель | Направление |
|------|--------|-------------|
| HTTP request body | `TaskCreate` | Client → API |
| HTTP response body | `TaskResponse` | API → Client |
| Service input | `TaskCreate` | Endpoint → Service |
| Service output | `TaskResponse` | Service → Endpoint |
| Storage | `TaskResponse` | Service ↔ Storage |
| HTTP error 404 | `TaskNotFoundDetail` | Endpoint → Client |

Отдельных моделей `TaskUpdate`, `TaskListResponse` (с пагинацией) или внутренних entity-классов в проекте нет.

## Валидация на уровне кода

Валидация входных данных выполняется **до** вызова сервиса — FastAPI/Pydantic проверяют `TaskCreate` при парсинге тела запроса.

`TaskResponse` валидируется при создании в `TaskService` и при десериализации ответа в тестах. Поля `title` и `priority` в ответе дублируют ограничения `TaskCreate`, что защищает от некорректных данных при прямой записи в storage (в текущем коде запись идёт только из сервиса).

## Тестовое покрытие моделей

Файл `tests/unit/test_models.py` проверяет:

- валидный `TaskCreate` с опциональным `description`;
- отклонение короткого/пустого `title`;
- отклонение слишком длинного `title` (>100);
- отклонение `priority` вне 1–5;
- создание валидного `TaskResponse`.
