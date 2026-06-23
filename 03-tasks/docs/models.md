# Модели и типы данных

Все модели — **Pydantic v2**. Размещаются в `api/schemas.py`.

ORM не используется — только DTO для запросов и ответов.

---

## Входная модель

### `TaskCreate`

Модель тела запроса при создании задачи (`POST /tasks`).

| Поле | Тип | Обязательное | Валидация | Описание |
|------|-----|--------------|-----------|----------|
| `title` | `string` | да | 3–100 символов | Название задачи |
| `description` | `string` | нет | — | Описание задачи |
| `priority` | `int` | да | 1–5 | Приоритет (1 — низкий, 5 — высокий) |

```python
from pydantic import BaseModel, Field


class TaskCreate(BaseModel):
  title: str = Field(
    ...,
    min_length=3,
    max_length=100,
    description="Название задачи",
    examples=["Настроить CI/CD"],
  )
  description: str | None = Field(
    default=None,
    description="Описание задачи",
    examples=["Добавить GitHub Actions для автотестов"],
  )
  priority: int = Field(
    ...,
    ge=1,
    le=5,
    description="Приоритет от 1 (низкий) до 5 (высокий)",
    examples=[3],
  )
```

### Примеры валидации `TaskCreate`

| Вход | Результат |
|------|-----------|
| `title: "ab"` | `422` — слишком короткий заголовок |
| `title: "a" * 101` | `422` — слишком длинный заголовок |
| `priority: 0` | `422` — значение вне диапазона |
| `priority: 6` | `422` — значение вне диапазона |
| `description` отсутствует | `null` в ответе — поле опционально |

---

## Выходная модель

### `TaskResponse`

Модель ответа API. Содержит все поля `TaskCreate` плюс системные.

| Поле | Тип | Описание |
|------|-----|----------|
| `id` | `int` | Уникальный идентификатор (генерируется сервисом) |
| `title` | `string` | Название задачи |
| `description` | `string \| null` | Описание задачи |
| `priority` | `int` | Приоритет 1–5 |
| `created_at` | `datetime` | Время создания в формате ISO 8601 |

```python
from datetime import datetime

from pydantic import BaseModel, Field


class TaskResponse(BaseModel):
  id: int = Field(..., description="Уникальный идентификатор задачи")
  title: str = Field(..., min_length=3, max_length=100)
  description: str | None = None
  priority: int = Field(..., ge=1, le=5)
  created_at: datetime = Field(..., description="Дата и время создания (ISO 8601)")

  model_config = {"json_schema_extra": {
    "examples": [{
      "id": 1,
      "title": "Настроить CI/CD",
      "description": "Добавить GitHub Actions для автотестов",
      "priority": 3,
      "created_at": "2026-06-23T12:00:00",
    }]
  }}
```

### Сериализация `created_at`

FastAPI сериализует `datetime` в ISO 8601 автоматически:

```json
"created_at": "2026-06-23T12:00:00"
```

---

## Внутренняя модель (опционально)

При росте проекта можно выделить доменную сущность в `services/`:

```python
# services/models.py (опционально, не обязательно для MVP)

from dataclasses import dataclass
from datetime import datetime


@dataclass
class Task:
  id: int
  title: str
  description: str | None
  priority: int
  created_at: datetime
```

Для MVP достаточно `TaskResponse` как единственной модели сущности — маппинг выполняется в `TaskService`.

---

## Модель ошибки

### `TaskNotFoundDetail`

Структура тела ответа при `404 Not Found` (задача не найдена).

```python
class TaskNotFoundDetail(BaseModel):
  detail: str = "Task not found"
  task_id: int
```

Используется при выбросе `HTTPException`:

```python
raise HTTPException(
  status_code=404,
  detail={"detail": "Task not found", "task_id": task_id},
)
```

---

## Промпт: генерация моделей данных

> Сгенерируй Pydantic-модели для системы управления задачами.
>
> **Модели:**
> - `TaskCreate` — входные данные (тело запроса)
> - `TaskResponse` — выходные данные (тело ответа)
>
> **Поля:**
> - `title`: `string`, обязательное, длина 3–100 символов
> - `description`: `string`, необязательное
> - `priority`: `int`, обязательное, диапазон 1–5
> - `created_at`: `datetime`, только в `TaskResponse`, формат ISO 8601
> - `id`: `int`, только в `TaskResponse`
>
> **Ограничения:**
> - Использовать Pydantic
> - Применить валидацию полей
> - Не использовать ORM
