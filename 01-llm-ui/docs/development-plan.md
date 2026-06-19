# План построения проекта

Пошаговый план от пустого репозитория до рабочего MVP с тестами.

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
   openai>=1.55.0
   streamlit>=1.40.0
   httpx>=0.28.0
   python-dotenv>=1.0.0

   # dev
   pytest>=8.3.0
   pytest-asyncio>=0.24.0
   ```

3. Создать `.env.example` и `.gitignore` (`.env`, `.venv`, `__pycache__`).
4. Создать виртуальное окружение и установить зависимости.

**Критерий готовности:** `pip install -r requirements.txt` проходит без ошибок.

---

## Этап 1. Конфигурация (`config/`)

**Цель:** централизованные настройки из `.env`.

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

     openai_api_key: str
     openai_model: str = "gpt-4o-mini"
     openai_temperature: float = 0.3
     openai_timeout_seconds: int = 30

     api_host: str = "0.0.0.0"
     api_port: int = 8000
     api_base_url: str = "http://localhost:8000"


   @lru_cache
   def get_settings() -> Settings:
     return Settings()
   ```

2. Создать `.env` с реальным `OPENAI_API_KEY`.

**Критерий готовности:** `from config.settings import get_settings; get_settings()` читает переменные.

**Тесты:** unit-тест с `monkeypatch` для env-переменных.

---

## Этап 2. Модели и схемы (`api/schemas.py`)

**Цель:** типизированный контракт входа/выхода.

**Задачи:**

1. Реализовать enum `UsageProfile`, `UpgradeUrgency`.
2. Реализовать `RecommendRequest` с валидаторами.
3. Реализовать `LLMRecommendationPayload`, `RecommendResponse`.
4. Реализовать `to_api_response()`.

**Критерий готовности:** Pydantic-модели импортируются, валидация работает.

**Тесты:** `tests/unit/test_models.py` — валидные/невалидные кейсы для каждого поля.

---

## Этап 3. LLM-слой (`llm/`)

**Цель:** изолированная работа с OpenAI.

**Задачи:**

1. `llm/prompts.py` — system prompt, `build_user_prompt()`.
2. `llm/client.py` — `OpenAIClient` с async-вызовом.
3. `llm/parser.py` — `parse_llm_response()`, `strip_markdown_json()`.
4. `services/exceptions.py` — `LLMError`, `LLMParseError`.

**Критерий готовности:** можно вызвать клиент из скрипта и получить JSON.

**Тесты:**

- `test_prompts.py` — подстановка переменных в шаблон.
- `test_parser.py` — парсинг валидного/невалидного JSON, markdown-обёртка.
- Клиент — мок через `pytest` + `unittest.mock` (не вызывать реальный API в unit-тестах).

---

## Этап 4. Бизнес-логика (`services/`)

**Цель:** оркестрация сценария рекомендации.

**Задачи:**

1. `services/recommendation.py` — класс `RecommendationService`.
2. Dependency injection: `get_recommendation_service()` для FastAPI `Depends`.
3. Обрезка рекомендаций, маппинг в API-ответ.

**Критерий готовности:** `await service.recommend(request)` возвращает `RecommendResponse`.

**Тесты:** `tests/integration/test_recommendation_service.py` с замоканным LLM-клиентом.

---

## Этап 5. API (`api/`, `main.py`)

**Цель:** HTTP-эндпоинт `POST /recommend`.

**Задачи:**

1. `api/endpoints/recommend.py` — эндпоинт с обработкой ошибок.
2. `api/router.py` — регистрация маршрутов.
3. `main.py` — создание `FastAPI`, подключение роутера.
4. Опционально: `GET /health`.

**Критерий готовности:**

```bash
uvicorn main:app --reload
curl -X POST http://localhost:8000/recommend \
  -H "Content-Type: application/json" \
  -d '{"current_phone":"iPhone 12","usage_profile":"gaming"}'
```

**Тесты:** `tests/integration/test_recommend_api.py` с `httpx.AsyncClient` и моком сервиса.

---

## Этап 6. Streamlit UI (`ui/`)

**Цель:** пользовательский интерфейс.

**Задачи:**

1. `ui/app.py` — форма, вызов API, отображение результата.
2. Конфигурация `API_BASE_URL` из env.
3. Обработка ошибок API (422, 502, сеть).

**Критерий готовности:** пользователь вводит данные → видит рекомендации или «обновление не требуется».

Подробнее: [streamlit-ui.md](./streamlit-ui.md).

---

## Этап 7. Тестирование и качество

**Цель:** покрытие ключевых сценариев.

**Задачи:**

1. `tests/conftest.py` — фикстуры: `client`, `mock_llm`, `sample_request`.
2. Unit-тесты: модели, промпты, парсер.
3. Интеграционные: API с моком, сервис с моком.
4. Опционально: 1 smoke-тест с реальным OpenAI (помечен `@pytest.mark.live`, запуск вручную).

**Критерий готовности:** `pytest` проходит зелёным.

Подробнее: [testing.md](./testing.md).

---

## Этап 8. Финализация

**Цель:** готовность к демонстрации и сдаче.

**Задачи:**

1. Проверить `.env.example` — все переменные задокументированы.
2. Добавить `README.md` в корень `01-llm-ui/` с инструкцией запуска.
3. Прогнать ручные сценарии:
   - флагман + everyday → `not_needed`;
   - старый телефон + gaming → рекомендации;
   - pro_photography + бюджет → рекомендации с учётом бюджета;
   - пустой `current_phone` → 422.
4. Проверить Swagger UI (`/docs`).

---

## Порядок зависимостей этапов

```
Этап 0 → Этап 1 → Этап 2 → Этап 3 → Этап 4 → Этап 5 → Этап 6
                              ↘         ↗
                            Этап 7 (параллельно с 4–6)
                                        ↓
                                    Этап 8
```

## Оценка трудозатрат

| Этап | Оценка |
|------|--------|
| 0–1 | 1–2 ч |
| 2 | 2–3 ч |
| 3 | 3–4 ч |
| 4 | 2 ч |
| 5 | 2 ч |
| 6 | 3–4 ч |
| 7 | 3–4 ч |
| 8 | 1–2 ч |
| **Итого** | **~17–22 ч** |

## Возможные улучшения (вне MVP)

- Кэширование ответов по `(current_phone, usage_profile)` (Redis / in-memory).
- История запросов в SQLite.
- Structured Outputs с жёсткой JSON Schema вместо `json_object`.
- Rate limiting на эндпоинте.
- Docker Compose (API + UI).
- Локализация UI на переключение языка.
