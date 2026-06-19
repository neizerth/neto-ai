# Рекомендательный сервис смартфонов

FastAPI + OpenAI + Streamlit. Подробная документация — в [docs/](./docs/README.md).

## Быстрый старт

```bash
cd 01-llm-ui
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# Заполните OPENAI_API_KEY в .env
```

### Запуск API

```bash
uvicorn main:app --reload --port 8000
```

Swagger UI: http://localhost:8000/docs

### Запуск UI

```bash
API_BASE_URL=http://localhost:8000 streamlit run ui/app.py
```

## Тесты

```bash
OPENAI_API_KEY=test-key pytest
```

Для unit/integration тестов реальный API-ключ не используется — достаточно любого значения в env.

## Структура

```
api/        — HTTP-эндпоинты
services/   — бизнес-логика
llm/        — промпты, клиент OpenAI, парсер
config/     — настройки из .env
ui/         — Streamlit-интерфейс
tests/      — unit и integration тесты
```
