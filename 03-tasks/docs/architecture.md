# Архитектура

## Обзор

```
┌──────────────┐   POST /tasks      ┌─────────────────┐
│   Клиент     │ ─────────────────► │   FastAPI       │
│ (curl, UI)   │   GET /tasks       │   api/          │
│              │ ◄───────────────── │                 │
└──────────────┘   GET /tasks/{id}  └────────┬────────┘
                                             │
                                    ┌────────▼────────┐
                                    │  TaskService    │
                                    │  services/      │
                                    └────────┬────────┘
                                             │
                                    ┌────────▼────────┐
                                    │ InMemoryStorage │
                                    │  dict[int, Task]│
                                    └─────────────────┘
```

## Слои и ответственность

### `api/` — транспортный слой

| Модуль | Назначение |
|--------|------------|
| `router.py` | Сборка маршрутов |
| `schemas.py` | Pydantic DTO: `TaskCreate`, `TaskResponse` |
| `endpoints/tasks.py` | HTTP-обработчики: создание, список, получение по ID |

**Делает:**

- Принимает HTTP-запросы, возвращает HTTP-ответы.
- Валидирует вход через Pydantic (`TaskCreate`).
- Делегирует работу `TaskService`.
- Преобразует «задача не найдена» в `HTTPException(404)`.

**Не делает:** генерацию ID, хранение данных, бизнес-правил.

### `services/` — бизнес-логика

| Модуль | Назначение |
|--------|------------|
| `task.py` | `TaskService`: create, get, list |
| `storage.py` | In-memory хранилище (`dict[int, TaskResponse]`) |

**Делает:**

- Генерирует монотонно возрастающий `id`.
- Проставляет `created_at` при создании.
- Ищет задачу по `task_id`, возвращает `None` если не найдена.

**Не делает:** работы с HTTP, чтения query/path-параметров.

### `config/` — конфигурация

- `Settings` на базе `pydantic-settings` (опционально для MVP).
- Параметры: `api_host`, `api_port`.
- Единственная точка доступа к настройкам (`get_settings()` с кэшированием).

## Поток данных

### Создание задачи

1. Клиент отправляет `TaskCreate` на `POST /tasks`.
2. FastAPI валидирует тело запроса (Pydantic). При ошибке — `422`.
3. `TaskService.create_task()`:
   - инкрементирует счётчик ID;
   - создаёт `TaskResponse` с `created_at=datetime.now(UTC)`;
   - сохраняет в `InMemoryStorage`.
4. API возвращает `201` с `TaskResponse`.

### Получение списка

1. Клиент вызывает `GET /tasks`.
2. `TaskService.list_tasks()` возвращает все значения из хранилища.
3. API возвращает `200` с `list[TaskResponse]`.

### Получение по ID

1. Клиент вызывает `GET /tasks/{task_id}`.
2. `TaskService.get_task(task_id)` ищет в хранилище.
3. Если `None` — эндпоинт выбрасывает `HTTPException(404)` с телом `{"detail": "Task not found", "task_id": ...}`.
4. Иначе — `200` с `TaskResponse`.

## Зависимости между модулями

```
config/settings.py
       │
       ▼
services/storage.py ◄── services/task.py
       ▲                      │
       │                      ▼
       └──────────── api/endpoints/tasks.py
                              │
                              ▼
                       api/schemas.py
                              │
                              ▼
                          main.py
```

**Правило:** зависимости направлены внутрь. `api/` зависит от `services/`, но не наоборот.

## In-memory хранилище

```python
# services/storage.py

class InMemoryStorage:
  def __init__(self) -> None:
    self._tasks: dict[int, TaskResponse] = {}
    self._next_id: int = 1

  def save(self, task: TaskResponse) -> TaskResponse:
    self._tasks[task.id] = task
    return task

  def get(self, task_id: int) -> TaskResponse | None:
    return self._tasks.get(task_id)

  def list_all(self) -> list[TaskResponse]:
    return list(self._tasks.values())

  def next_id(self) -> int:
    current = self._next_id
    self._next_id += 1
    return current
```

**Ограничения:**

- Данные не персистентны — теряются при перезапуске.
- Не потокобезопасно (достаточно для учебного MVP).
- Один экземпляр хранилища на процесс (singleton через `Depends`).

## Инъекция зависимостей

```python
# services/task.py

_storage = InMemoryStorage()


def get_task_service() -> TaskService:
  return TaskService(storage=_storage)
```

Один экземпляр хранилища разделяется между всеми запросами в рамках процесса.

## Расширение (вне scope MVP)

| Направление | Изменения |
|-------------|-----------|
| PostgreSQL | Заменить `InMemoryStorage` на репозиторий с SQLAlchemy/asyncpg |
| Пагинация | `GET /tasks?offset=0&limit=20` |
| Фильтрация | `GET /tasks?priority=5` |
| Обновление/удаление | `PUT /tasks/{id}`, `DELETE /tasks/{id}` |
| Аутентификация | Middleware или `Depends` с JWT |
