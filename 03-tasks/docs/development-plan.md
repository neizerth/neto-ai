# План построения проекта

Пошаговый план от пустого репозитория до рабочего MVP. Каждый этап сопровождается промптом для поэтапной генерации кода с помощью LLM.

---

## Этап 0. Подготовка окружения

**Цель:** базовая инфраструктура проекта.

**Задачи:**

1. Создать структуру каталогов (см. [README.md](./README.md)).
2. Инициализировать `requirements.txt`:

   ```
   fastapi>=0.115.0
   uvicorn[standard]>=0.32.0
   pydantic>=2.9.0
   pydantic-settings>=2.6.0

   # dev
   pytest>=8.3.0
   httpx>=0.28.0
   ```

3. Создать `.gitignore` (`.venv`, `__pycache__`, `.pytest_cache`).
4. Создать виртуальное окружение и установить зависимости.

**Критерий готовности:** `pip install -r requirements.txt` проходит без ошибок.

---

## Этап 1. Конфигурация (`config/`)

**Цель:** централизованные настройки приложения.

**Задачи:**

1. Реализовать `config/settings.py`:

   ```python
   from functools import lru_cache
   from pydantic_settings import BaseSettings, SettingsConfigDict


   class Settings(BaseSettings):
     model_config = SettingsConfigDict(
       env_file=".env",
       env_file_encoding="utf-8",
     )

     api_host: str = "0.0.0.0"
     api_port: int = 8000


   @lru_cache
   def get_settings() -> Settings:
     return Settings()
   ```

**Критерий готовности:** `from config.settings import get_settings; get_settings()` возвращает настройки.

---

## Этап 2. Модели данных (`api/schemas.py`)

**Цель:** Pydantic DTO с валидацией.

**Промпт:**

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

**Задачи:**

1. Создать `api/schemas.py` с `TaskCreate` и `TaskResponse` (см. [models.md](./models.md)).
2. Добавить `model_config` с примерами для Swagger.

**Критерий готовности:** unit-тесты валидируют граничные значения `title` и `priority`.

**Тесты:** `tests/unit/test_models.py`

---

## Этап 3. In-memory хранилище (`services/storage.py`)

**Цель:** персистентность в рамках процесса без БД.

**Задачи:**

1. Реализовать `InMemoryStorage` (см. [architecture.md](./architecture.md)).
2. Методы: `save`, `get`, `list_all`, `next_id`.

**Критерий готовности:** можно сохранить и извлечь задачу по ID в unit-тесте.

---

## Этап 4. Сервис задач (`services/task.py`)

**Цель:** бизнес-логика создания и чтения задач.

**Задачи:**

1. Реализовать `TaskService`:

   ```python
   class TaskService:
     def __init__(self, storage: InMemoryStorage) -> None:
       self._storage = storage

     def create_task(self, payload: TaskCreate) -> TaskResponse:
       task = TaskResponse(
         id=self._storage.next_id(),
         title=payload.title,
         description=payload.description,
         priority=payload.priority,
         created_at=datetime.now(timezone.utc),
       )
       return self._storage.save(task)

     def get_task(self, task_id: int) -> TaskResponse | None:
       return self._storage.get(task_id)

     def list_tasks(self) -> list[TaskResponse]:
       return self._storage.list_all()
   ```

2. Реализовать `get_task_service()` для DI.

**Критерий готовности:** unit-тесты покрывают create, get (found/not found), list.

**Тесты:** `tests/unit/test_task_service.py`

---

## Этап 5. POST-эндпоинт (`api/endpoints/tasks.py`)

**Цель:** создание задачи через HTTP.

**Промпт:**

> Создай FastAPI-эндпоинт для создания задачи.
>
> **Метод и путь:** `POST /tasks`
>
> **Входные данные:** тело запроса — модель `TaskCreate`
>
> **Ответ `201 Created`:** модель `TaskResponse`
>
> **Ограничения:**
> - Использовать ранее определённые Pydantic-модели
> - Делегировать логику `TaskService`
> - Не подключать реальную БД

**Задачи:**

1. Создать `api/endpoints/tasks.py` с `POST /tasks`.
2. Подключить роутер в `api/router.py`.
3. Создать `main.py` с `FastAPI` и подключением роутера.

**Критерий готовности:** `curl -X POST http://localhost:8000/tasks -H "Content-Type: application/json" -d '{"title":"Test task","priority":3}'` возвращает `201`.

---

## Этап 6. GET-эндпоинты

**Цель:** получение списка и одной задачи.

### 6a. Список задач

**Промпт:**

> Создай FastAPI-эндпоинт для получения списка всех задач.
>
> **Метод и путь:** `GET /tasks`
>
> **Ответ `200 OK`:** массив `TaskResponse`
>
> **Ограничения:**
> - Делегировать логику `TaskService`
> - Не подключать реальную БД

### 6b. Задача по ID

**Промпт:**

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

**Критерий готовности:**

- `GET /tasks` возвращает все созданные задачи.
- `GET /tasks/1` возвращает задачу с `id=1`.
- `GET /tasks/999` возвращает `404`.

---

## Этап 7. Обработка ошибок

**Цель:** единообразный ответ при отсутствии задачи.

**Промпт:**

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

**Задачи:**

1. В `get_task` выбрасывать `HTTPException(status_code=404, detail={...})`.
2. Убедиться, что тело ответа соответствует контракту (см. [api.md](./api.md)).

**Критерий готовности:** интеграционный тест проверяет структуру `404`-ответа.

**Тесты:** `tests/integration/test_tasks_api.py`

---

## Этап 8. Интеграционные тесты

**Цель:** сквозная проверка API.

**Задачи:**

1. `conftest.py` — `TestClient` с чистым хранилищем на каждый тест.
2. Сценарии:
   - создание задачи → `201`, корректное тело;
   - создание с невалидным `title` → `422`;
   - список после создания двух задач → `200`, длина `2`;
   - получение существующей задачи → `200`;
   - получение несуществующей → `404` с `task_id`.

**Критерий готовности:** `pytest` проходит без ошибок.

---

## Чеклист MVP

- [ ] `TaskCreate` и `TaskResponse` с валидацией
- [ ] `POST /tasks` → `201`
- [ ] `GET /tasks` → `200`, список
- [ ] `GET /tasks/{task_id}` → `200` или `404`
- [ ] `404` с `{"detail": "Task not found", "task_id": N}`
- [ ] In-memory хранилище, без БД
- [ ] Разделение `api/` / `services/` / `config/`
- [ ] Unit- и интеграционные тесты
