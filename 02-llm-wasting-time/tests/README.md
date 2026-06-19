# Тесты (TDD)

На этапе GREEN все **101** тест проходят.

## Структура

| Каталог | Назначение |
|---------|------------|
| `unit/` | Схемы, промпты, PromptBuilder, исключения |
| `integration/` | Сервисы + HTTP API (с моками LLM / DI) |
| `e2e/` | Сквозные сценарии через реальный стек (SQLite + API) |

## Запуск

```bash
cd 02-llm-wasting-time
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Все тесты (ожидается RED)
pytest -v

# Только unit
pytest tests/unit/ -v

# Только integration
pytest tests/integration/ -v

# Только e2e
pytest tests/e2e/ -m e2e -v
```

## Порядок реализации (GREEN)

Рекомендуемый порядок для перевода тестов в зелёное состояние:

1. `api/schemas.py`, `llm/schemas.py`
2. `config/settings.py`, `config/database.py`
3. `llm/prompts.py`, `services/prompt_builder_service.py`
4. `llm/openai_provider.py` (и мок в тестах)
5. `services/profile_service.py`, `feedback_service.py`, `recommendation_service.py`
6. `api/*.py` — эндпоинты с обработкой исключений
7. E2E — подключить in-memory SQLite в `conftest` для e2e-фикстуры
