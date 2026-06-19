# Стратегия тестирования

## Структура

```
tests/
├── conftest.py              # Общие фикстуры
├── unit/
│   ├── test_models.py       # Pydantic-валидация
│   ├── test_prompts.py      # Шаблоны промптов
│   └── test_parser.py       # Парсинг ответа LLM
└── integration/
    ├── test_recommend_api.py        # HTTP-эндпоинт
    └── test_recommendation_service.py  # Сервис с моком LLM
```

## Фикстуры (`conftest.py`)

```python
import pytest
from httpx import ASGITransport, AsyncClient
from unittest.mock import AsyncMock

from main import app
from api.schemas import RecommendRequest, UsageProfile
from services.recommendation import get_recommendation_service


@pytest.fixture
def sample_request() -> RecommendRequest:
  return RecommendRequest(
    current_phone="iPhone 12",
    usage_profile=UsageProfile.GAMING,
    max_recommendations=3,
  )


@pytest.fixture
def valid_llm_json() -> str:
  return """{
    "upgrade_needed": true,
    "urgency": "recommended",
    "summary": "iPhone 12 уступает в играх современным флагманам.",
    "current_phone_assessment": "Устройство 2020 года с A14 Bionic.",
    "recommendations": [
      {
        "brand": "Apple",
        "model": "iPhone 16 Pro",
        "full_name": "Apple iPhone 16 Pro",
        "reason": "A18 Pro, 120 Гц, лучшее охлаждение.",
        "estimated_price_range": "110 000–130 000 ₽"
      }
    ]
  }"""


@pytest.fixture
async def client():
  transport = ASGITransport(app=app)
  async with AsyncClient(transport=transport, base_url="http://test") as ac:
    yield ac
```

---

## Unit-тесты: модели

```python
# tests/unit/test_models.py

import pytest
from pydantic import ValidationError
from api.schemas import RecommendRequest, UsageProfile, LLMRecommendationPayload


def test_valid_request(sample_request):
  assert sample_request.current_phone == "iPhone 12"


@pytest.mark.parametrize("phone", ["", " ", "a"])
def test_invalid_phone_too_short(phone):
  with pytest.raises(ValidationError):
    RecommendRequest(current_phone=phone, usage_profile=UsageProfile.EVERYDAY)


def test_phone_normalization():
  req = RecommendRequest(
    current_phone="  iPhone   12  ",
    usage_profile=UsageProfile.EVERYDAY,
  )
  assert req.current_phone == "iPhone 12"


def test_upgrade_not_needed_empty_recommendations():
  payload = LLMRecommendationPayload.model_validate({
    "upgrade_needed": False,
    "urgency": "not_needed",
    "summary": "Телефон отлично подходит.",
    "current_phone_assessment": "Флагман 2023 года.",
    "recommendations": [],
  })
  assert not payload.upgrade_needed


def test_upgrade_not_needed_with_recommendations_fails():
  with pytest.raises(ValidationError):
    LLMRecommendationPayload.model_validate({
      "upgrade_needed": False,
      "urgency": "not_needed",
      "summary": "Тест.",
      "current_phone_assessment": "Тест.",
      "recommendations": [{"brand": "A", "model": "B", "full_name": "A B", "reason": "x" * 10}],
    })
```

---

## Unit-тесты: промпты

```python
# tests/unit/test_prompts.py

from llm.prompts import build_user_prompt


def test_build_user_prompt_contains_phone():
  prompt = build_user_prompt("iPhone 12", "gaming", 3, None)
  assert "iPhone 12" in prompt
  assert "Игры" in prompt
  assert "3" in prompt


def test_build_user_prompt_with_additional():
  prompt = build_user_prompt("iPhone 12", "gaming", 3, "Бюджет 100к")
  assert "Бюджет 100к" in prompt
```

---

## Unit-тесты: парсер

```python
# tests/unit/test_parser.py

import pytest
from llm.parser import parse_llm_response, strip_markdown_json, LLMParseError


def test_parse_valid_json(valid_llm_json):
  payload = parse_llm_response(valid_llm_json)
  assert payload.upgrade_needed is True
  assert len(payload.recommendations) == 1


def test_parse_invalid_json():
  with pytest.raises(LLMParseError):
    parse_llm_response("not json")


def test_strip_markdown():
  raw = '```json\n{"upgrade_needed": false}\n```'
  assert '"upgrade_needed"' in strip_markdown_json(raw)
```

---

## Интеграционные тесты: API

```python
# tests/integration/test_recommend_api.py

import pytest
from unittest.mock import AsyncMock, patch
from api.schemas import RecommendResponse, UpgradeUrgency, UsageProfile


@pytest.mark.asyncio
async def test_recommend_success(client, valid_llm_json):
  mock_response = RecommendResponse(
    upgrade_needed=True,
    urgency=UpgradeUrgency.RECOMMENDED,
    summary="Тест.",
    current_phone_assessment="Тест.",
    recommendations=[],
    usage_profile=UsageProfile.GAMING,
    current_phone="iPhone 12",
  )

  with patch(
    "api.endpoints.recommend.RecommendationService.recommend",
    new_callable=AsyncMock,
    return_value=mock_response,
  ):
    response = await client.post(
      "/recommend",
      json={"current_phone": "iPhone 12", "usage_profile": "gaming"},
    )

  assert response.status_code == 200
  assert response.json()["upgrade_needed"] is True


@pytest.mark.asyncio
async def test_recommend_validation_error(client):
  response = await client.post(
    "/recommend",
    json={"current_phone": "", "usage_profile": "gaming"},
  )
  assert response.status_code == 422
```

---

## Интеграционные тесты: сервис

```python
# tests/integration/test_recommendation_service.py

import pytest
from unittest.mock import AsyncMock

from services.recommendation import RecommendationService
from api.schemas import RecommendRequest, UsageProfile


@pytest.mark.asyncio
async def test_service_recommend(sample_request, valid_llm_json):
  mock_client = AsyncMock()
  mock_client.get_recommendation_json.return_value = valid_llm_json

  service = RecommendationService(mock_client)
  result = await service.recommend(sample_request)

  assert result.upgrade_needed is True
  assert result.current_phone == "iPhone 12"
  mock_client.get_recommendation_json.assert_called_once()
```

---

## Live-тест (опционально)

Тест с реальным OpenAI API — только для ручного запуска:

```python
# tests/integration/test_live_openai.py

import pytest
from config.settings import get_settings
from llm.client import OpenAIClient
from llm.prompts import build_user_prompt
from llm.parser import parse_llm_response


@pytest.mark.live
@pytest.mark.asyncio
async def test_real_openai_call():
  settings = get_settings()
  client = OpenAIClient(settings)
  prompt = build_user_prompt("iPhone 12", "gaming", 2, None)
  raw = await client.get_recommendation_json(prompt)
  payload = parse_llm_response(raw)
  assert payload.summary
```

Запуск:

```bash
pytest -m live tests/integration/test_live_openai.py
```

---

## Запуск тестов

```bash
# Все тесты (без live)
pytest

# С покрытием
pytest --cov=. --cov-report=term-missing

# Только unit
pytest tests/unit/

# Verbose
pytest -v
```

## `pytest.ini`

```ini
[pytest]
asyncio_mode = auto
markers =
    live: тесты с реальным OpenAI API (запуск вручную)
```

## Что покрывать обязательно

| Область | Кейсы |
|---------|-------|
| Валидация входа | пустой телефон, слишком длинные поля, невалидный enum |
| Консистентность LLM-ответа | `upgrade_needed=false` + пустой список |
| Парсер | валидный JSON, битый JSON, markdown-обёртка |
| API | 200, 422, 502 (мок ошибки LLM) |
| Сервис | обрезка рекомендаций до `max_recommendations` |
