# API-спецификация

Базовый URL: `http://localhost:8000` (настраивается через `config/settings.py`).

Интерактивная документация: `http://localhost:8000/docs` (Swagger UI).

---

## `POST /tasks`

Создать новую задачу.

### Request

**Headers:**

```
Content-Type: application/json
```

**Body:**

```json
{
  "title": "Настроить CI/CD",
  "description": "Добавить GitHub Actions для автотестов",
  "priority": 3
}
```

| Поле | Тип | Обязательное | Описание |
|------|-----|--------------|----------|
| `title` | `string` | да | Название, 3–100 символов |
| `description` | `string` | нет | Описание задачи |
| `priority` | `integer` | да | Приоритет 1–5 |

### Response `201 Created`

```json
{
  "id": 1,
  "title": "Настроить CI/CD",
  "description": "Добавить GitHub Actions для автотестов",
  "priority": 3,
  "created_at": "2026-06-23T12:00:00"
}
```

| Поле | Тип | Описание |
|------|-----|----------|
| `id` | `int` | Сгенерированный идентификатор |
| `title` | `string` | Название задачи |
| `description` | `string \| null` | Описание |
| `priority` | `int` | Приоритет 1–5 |
| `created_at` | `string` | ISO 8601 |

### Коды ошибок

#### `422 Unprocessable Entity`

Ошибка валидации входных данных (автоматически через Pydantic/FastAPI).

```json
{
  "detail": [
    {
      "type": "string_too_short",
      "loc": ["body", "title"],
      "msg": "String should have at least 3 characters",
      "input": "ab"
    }
  ]
}
```

---

## `GET /tasks`

Получить список всех задач.

### Request

Параметры и тело отсутствуют.

### Response `200 OK`

```json
[
  {
    "id": 1,
    "title": "Настроить CI/CD",
    "description": "Добавить GitHub Actions для автотестов",
    "priority": 3,
    "created_at": "2026-06-23T12:00:00"
  },
  {
    "id": 2,
    "title": "Написать документацию",
    "description": null,
    "priority": 2,
    "created_at": "2026-06-23T12:05:00"
  }
]
```

Пустой список, если задач нет:

```json
[]
```

---

## `GET /tasks/{task_id}`

Получить задачу по идентификатору.

### Request

| Параметр | Расположение | Тип | Обязательный | Описание |
|----------|--------------|-----|--------------|----------|
| `task_id` | path | `int` | да | Идентификатор задачи |

### Response `200 OK`

```json
{
  "id": 1,
  "title": "Настроить CI/CD",
  "description": "Добавить GitHub Actions для автотестов",
  "priority": 3,
  "created_at": "2026-06-23T12:00:00"
}
```

### Коды ошибок

#### `404 Not Found`

Задача с указанным `task_id` не найдена.

```json
{
  "detail": "Task not found",
  "task_id": 42
}
```

**Ограничения реализации:**

- Использовать встроенный `HTTPException` FastAPI.
- Не реализовывать глобальный middleware для этой цели.

### Промпт: генерация эндпоинта получения задачи (GET)

> Создай FastAPI-эндпоинт для получения задачи по идентификатору.
>
> **Метод и путь:** `GET /tasks/{task_id}`
>
> **Входные данные:**
> - `task_id` (path, `int`, обязательный)
>
> **Ответ `200 OK`:**
> - `id`: `int`
> - `title`: `string`
> - `description`: `string | null`
> - `priority`: `int`
> - `created_at`: `string` (ISO 8601)
>
> **Логика:**
> - Если задача найдена — вернуть `TaskResponse`
> - Если не найдена — `404 Not Found`
>
> **Ограничения:**
> - Использовать ранее определённые Pydantic-модели
> - Не подключать реальную БД

---

## Обработка ошибок

### Сводка HTTP-кодов

| Код | Сценарий | Кто формирует |
|-----|----------|---------------|
| `201` | Задача успешно создана | Эндпоинт `POST /tasks` |
| `200` | Задача(и) найдены | Эндпоинты `GET` |
| `404` | Задача не найдена | `HTTPException` в эндпоинте/сервисе |
| `422` | Невалидные входные данные | FastAPI + Pydantic (автоматически) |

### Промпт: генерация обработки ошибок

> Дополни API обработкой ошибок.
>
> **Требование:** если задача не найдена, вернуть JSON с кодом `404 Not Found`:
>
> ```json
> {
>   "detail": "Task not found",
>   "task_id": int
> }
> ```
>
> **Ограничения:**
> - Использовать встроенный `HTTPException` FastAPI
> - Не реализовывать глобальный middleware

---

## Реализация эндпоинтов

```python
# api/endpoints/tasks.py

from fastapi import APIRouter, Depends, HTTPException, status

from api.schemas import TaskCreate, TaskResponse
from services.task import TaskService, get_task_service

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post(
  "",
  response_model=TaskResponse,
  status_code=status.HTTP_201_CREATED,
  summary="Создать задачу",
)
def create_task(
  payload: TaskCreate,
  service: TaskService = Depends(get_task_service),
) -> TaskResponse:
  return service.create_task(payload)


@router.get(
  "",
  response_model=list[TaskResponse],
  summary="Список задач",
)
def list_tasks(
  service: TaskService = Depends(get_task_service),
) -> list[TaskResponse]:
  return service.list_tasks()


@router.get(
  "/{task_id}",
  response_model=TaskResponse,
  summary="Получить задачу по ID",
)
def get_task(
  task_id: int,
  service: TaskService = Depends(get_task_service),
) -> TaskResponse:
  task = service.get_task(task_id)
  if task is None:
    raise HTTPException(
      status_code=404,
      detail={"detail": "Task not found", "task_id": task_id},
    )
  return task
```

```python
# api/router.py

from fastapi import APIRouter
from api.endpoints import tasks

api_router = APIRouter()
api_router.include_router(tasks.router)
```

```python
# main.py

from fastapi import FastAPI
from api.router import api_router

app = FastAPI(
  title="Task Management API",
  description="Минимальный REST API для управления задачами",
  version="1.0.0",
)
app.include_router(api_router)
```

---

## Health-check (опционально)

### `GET /health`

```json
{
  "status": "ok"
}
```

Не обращается к хранилищу — только проверяет, что процесс API жив.
