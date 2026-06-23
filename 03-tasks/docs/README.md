# Task Management API

Минимальный REST API для управления задачами. Позволяет создавать задачи, получать список и читать задачу по идентификатору. Данные хранятся в памяти процесса — без базы данных и внешних зависимостей.

## Содержание документации

| Документ | Описание |
|----------|----------|
| [architecture.md](./architecture.md) | Архитектура, технологии, поток данных |
| [models.md](./models.md) | Pydantic-модели, DTO, валидация |
| [api.md](./api.md) | Контракт API, коды ответов, примеры запросов |

## Структура проекта

```
03-tasks/
├── main.py                 # Точка входа: создание FastAPI-приложения, health-check
├── requirements.txt        # Зависимости Python (FastAPI, Pydantic, pytest и др.)
├── pytest.ini              # Конфигурация pytest (pythonpath = .)
├── .gitignore              # Исключения для git (.env, .venv, __pycache__ и т.д.)
│
├── api/                    # HTTP-слой: маршруты и схемы запросов/ответов
│   ├── router.py           # Корневой APIRouter, подключает эндпоинты
│   ├── schemas.py          # Pydantic-модели (DTO): TaskCreate, TaskResponse, TaskNotFoundDetail
│   └── endpoints/
│       └── tasks.py        # CRUD-эндпоинты для /tasks
│
├── services/               # Бизнес-логика и хранилище
│   ├── task.py             # TaskService: создание, чтение, список задач
│   └── storage.py          # InMemoryStorage: словарь задач в RAM
│
├── config/
│   └── settings.py         # Настройки приложения (host, port) через pydantic-settings
│
├── tests/
│   ├── conftest.py         # Фикстуры pytest: изолированное хранилище и TestClient
│   ├── unit/               # Юнит-тесты моделей и сервиса
│   │   ├── test_models.py
│   │   └── test_task_service.py
│   └── integration/        # Интеграционные тесты HTTP API
│       └── test_tasks_api.py
│
└── docs/                   # Документация проекта
```

### Краткое описание модулей

| Путь | Назначение |
|------|------------|
| `main.py` | Создаёт экземпляр `FastAPI`, подключает `api_router`, экспортирует эндпоинт `GET /health`. |
| `api/router.py` | Агрегирует роутеры эндпоинтов в единый `api_router`. |
| `api/schemas.py` | Контракты данных: входные DTO, ответы API, схема ошибки 404. |
| `api/endpoints/tasks.py` | Три эндпоинта: `POST /tasks`, `GET /tasks`, `GET /tasks/{task_id}`. |
| `services/task.py` | Генерация ID, проставление `created_at`, делегирование в хранилище. |
| `services/storage.py` | In-memory `dict[int, TaskResponse]` с автоинкрементом ID. |
| `config/settings.py` | Чтение `api_host` и `api_port` из переменных окружения / `.env`. |
| `tests/conftest.py` | Подмена `get_task_service` через `dependency_overrides` для изоляции тестов. |

## Быстрый старт

### Требования

- Python 3.11+ (в проекте используется 3.13)
- pip

### Установка и запуск

```bash
cd 03-tasks

# Виртуальное окружение
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# Зависимости
pip install -r requirements.txt

# Запуск сервера
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Опционально можно задать переменные в файле `.env`:

```env
API_HOST=0.0.0.0
API_PORT=8000
```

> **Примечание:** `Settings` определены в `config/settings.py`, но `main.py` пока не использует их для запуска uvicorn — хост и порт задаются аргументами командной строки.

### Проверка работоспособности

```bash
# Health-check
curl http://localhost:8000/health

# Интерактивная документация
open http://localhost:8000/docs      # Swagger UI
open http://localhost:8000/redoc    # ReDoc
```

### Запуск тестов

```bash
pytest
pytest -v                           # подробный вывод
pytest tests/unit/                  # только юнит-тесты
pytest tests/integration/           # только интеграционные
```

## Использование API (кратко)

```bash
# Создать задачу
curl -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{"title": "Настроить CI/CD", "description": "GitHub Actions", "priority": 3}'

# Список задач
curl http://localhost:8000/tasks

# Задача по ID
curl http://localhost:8000/tasks/1
```

Подробные примеры, коды ответов и схемы — в [api.md](./api.md).

## Ограничения

| Ограничение | Описание |
|-------------|----------|
| In-memory хранилище | Данные теряются при перезапуске процесса. Нет персистентности. |
| Только чтение и создание | Нет `PUT`/`PATCH`/`DELETE` — задачи нельзя обновить или удалить. |
| Один процесс | Глобальный синглтон `_storage` в `services/task.py` не рассчитан на несколько воркеров uvicorn с раздельной памятью. |
| Нет аутентификации | API открыт, без авторизации и rate limiting. |
| Нет пагинации и фильтрации | `GET /tasks` возвращает все задачи целиком, без сортировки. |
| Нет валидации `task_id` | Отрицательные или нулевые ID принимаются в path, но задача не будет найдена (404). |
| Настройки не подключены к запуску | `config/settings.py` существует, но `main.py` не читает host/port из настроек автоматически. |
| Нет CORS middleware | Для вызова из браузера с другого origin потребуется добавить `CORSMiddleware`. |

## Версия API

Версия приложения: **1.0.0** (задаётся в `main.py`).
