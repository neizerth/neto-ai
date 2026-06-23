# API

Базовый URL: `http://localhost:8000` (при запуске через uvicorn на порту 8000).

Префикса версии (`/api/v1`) нет — эндпоинты доступны с корня.

## Обзор эндпоинтов

| Метод | Путь | Код успеха | Описание |
|-------|------|------------|----------|
| `GET` | `/health` | 200 | Проверка доступности сервиса |
| `POST` | `/tasks` | 201 | Создать задачу |
| `GET` | `/tasks` | 200 | Список всех задач |
| `GET` | `/tasks/{task_id}` | 200 | Получить задачу по ID |

Аутентификация не требуется.

---

## GET /health

Liveness-check приложения.

**Ответ 200**

```json
{
  "status": "ok"
}
```

---

## POST /tasks

Создаёт новую задачу.

**Заголовки**

```
Content-Type: application/json
```

**Тело запроса** — см. [TaskCreate](./models.md#taskcreate--входной-dto)

**Ответ 201** — `TaskResponse`

```bash
curl -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Настроить CI/CD",
    "description": "Добавить GitHub Actions для автотестов",
    "priority": 3
  }'
```

```json
{
  "id": 1,
  "title": "Настроить CI/CD",
  "description": "Добавить GitHub Actions для автотестов",
  "priority": 3,
  "created_at": "2026-06-23T12:00:00+00:00"
}
```

**Ответ 422** — ошибка валидации

```bash
curl -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{"title": "ab", "priority": 3}'
```

Типичный фрагмент ответа:

```json
{
  "detail": [
    {
      "type": "string_too_short",
      "loc": ["body", "title"],
      "msg": "String should have at least 3 characters",
      "input": "ab",
      "ctx": {"min_length": 3}
    }
  ]
}
```

---

## GET /tasks

Возвращает массив всех задач. Порядок соответствует порядку вставки в `dict` (в CPython 3.7+ — порядок добавления ключей). Явная сортировка не гарантируется спецификацией API.

**Ответ 200** — `TaskResponse[]`

Пустое хранилище:

```json
[]
```

После создания двух задач:

```bash
curl http://localhost:8000/tasks
```

```json
[
  {
    "id": 1,
    "title": "Task one",
    "description": null,
    "priority": 1,
    "created_at": "2026-06-23T12:00:00+00:00"
  },
  {
    "id": 2,
    "title": "Task two",
    "description": null,
    "priority": 2,
    "created_at": "2026-06-23T12:01:00+00:00"
  }
]
```

---

## GET /tasks/{task_id}

Возвращает одну задачу по числовому идентификатору.

**Параметры пути**

| Параметр | Тип | Описание |
|----------|-----|----------|
| `task_id` | `int` | ID задачи |

**Ответ 200** — `TaskResponse`

```bash
curl http://localhost:8000/tasks/1
```

**Ответ 404** — задача не найдена

```bash
curl http://localhost:8000/tasks/999
```

```json
{
  "detail": {
    "detail": "Task not found",
    "task_id": 999
  }
}
```

---

## Коды ответов (сводка)

| Код | Когда возникает |
|-----|-----------------|
| **200** | Успешный `GET` |
| **201** | Задача успешно создана |
| **404** | Задача с указанным `task_id` не существует |
| **422** | Невалидное тело запроса (`TaskCreate`) |

Другие коды (401, 403, 500 с кастомной обработкой) в текущей реализации не используются.

---

## Интерактивная документация

После запуска сервера:

| URL | Инструмент |
|-----|------------|
| `/docs` | Swagger UI — можно вызывать эндпоинты из браузера |
| `/redoc` | ReDoc — читаемая спецификация |
| `/openapi.json` | Сырая OpenAPI 3.x схема |

Тег OpenAPI для задач: **`tasks`**.

---

## Пример сценария использования

```bash
# 1. Проверить, что сервер жив
curl http://localhost:8000/health

# 2. Создать задачи
curl -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{"title": "Изучить FastAPI", "priority": 5}'

curl -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{"title": "Написать тесты", "description": "unit + integration", "priority": 4}'

# 3. Получить список
curl http://localhost:8000/tasks

# 4. Получить задачу по ID
curl http://localhost:8000/tasks/1

# 5. Запрос несуществующей задачи
curl -i http://localhost:8000/tasks/42
# HTTP/1.1 404 Not Found
```

---

## Ограничения API

- Нет эндпоинтов обновления (`PUT`/`PATCH`) и удаления (`DELETE`).
- Нет query-параметров: фильтрация по приоритету, поиск по title, пагинация (`limit`/`offset`).
- Нет заголовков `ETag`, `Last-Modified` для кэширования.
- Данные не переживают перезапуск сервера.
- При запуске нескольких воркеров uvicorn (`--workers N`) у каждого воркера своё хранилище — списки задач будут расходиться.
