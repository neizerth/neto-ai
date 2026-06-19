# API-спецификация

Базовый URL: `http://localhost:8000` (настраивается через `.env`).

Интерактивная документация: `http://localhost:8000/docs` (Swagger UI).

## `POST /recommend`

Получить рекомендации по обновлению смартфона.

### Request

**Headers:**

```
Content-Type: application/json
```

**Body:**

```json
{
  "current_phone": "iPhone 12",
  "usage_profile": "pro_photography",
  "additional_requirements": "Бюджет до 120 000 ₽, предпочтительно компактный",
  "max_recommendations": 3
}
```

| Поле | Тип | Обязательное | По умолчанию | Описание |
|------|-----|--------------|--------------|----------|
| `current_phone` | `string` | да | — | Текущая модель телефона |
| `usage_profile` | `string` (enum) | да | — | Сценарий использования |
| `additional_requirements` | `string` | нет | `null` | Дополнительные пожелания |
| `max_recommendations` | `integer` | нет | `3` | Лимит рекомендаций (1–5) |

### Response `200 OK`

**Обновление рекомендуется:**

```json
{
  "upgrade_needed": true,
  "urgency": "recommended",
  "summary": "Для профессиональной фотографии iPhone 12 уже не обеспечивает достаточное качество в сложных условиях освещения и ограничен в ProRes/RAW-возможностях по сравнению с актуальными флагманами.",
  "current_phone_assessment": "iPhone 12 (2020) — хороший телефон для повседневной съёмки, но для pro-сценария уступает по сенсору, оптическому зуму и стабилизации.",
  "recommendations": [
    {
      "brand": "Apple",
      "model": "iPhone 16 Pro",
      "full_name": "Apple iPhone 16 Pro",
      "reason": "48 Мп основной сенсор, улучшенная стабилизация, ProRes и Apple Log, отличная экосистема для мобильной фотографии.",
      "estimated_price_range": "110 000–130 000 ₽"
    },
    {
      "brand": "Samsung",
      "model": "Galaxy S24 Ultra",
      "full_name": "Samsung Galaxy S24 Ultra",
      "reason": "Телефото 5x, RAW-съёмка, S Pen для точной настройки, гибкость Android для pro-воркфлоу.",
      "estimated_price_range": "100 000–120 000 ₽"
    }
  ],
  "usage_profile": "pro_photography",
  "current_phone": "iPhone 12"
}
```

**Обновление не требуется:**

```json
{
  "upgrade_needed": false,
  "urgency": "not_needed",
  "summary": "Samsung Galaxy S23 Ultra полностью закрывает ваш сценарий повседневного использования. Актуальные модели дают лишь инкрементальные улучшения, не оправдывающие стоимость обновления.",
  "current_phone_assessment": "Флагман 2023 года с отличным экраном, камерой и производительностью — более чем достаточен для everyday-сценария.",
  "recommendations": [],
  "usage_profile": "everyday",
  "current_phone": "Samsung Galaxy S23 Ultra"
}
```

### Коды ошибок

#### `422 Unprocessable Entity`

Ошибка валидации входных данных.

```json
{
  "detail": [
    {
      "type": "string_too_short",
      "loc": ["body", "current_phone"],
      "msg": "String should have at least 2 characters",
      "input": " "
    }
  ]
}
```

#### `502 Bad Gateway`

LLM вернула невалидный JSON или недоступна.

```json
{
  "detail": "Не удалось получить корректный ответ от модели",
  "error_code": "LLM_PARSE_ERROR"
}
```

#### `500 Internal Server Error`

Неожиданная ошибка сервера.

```json
{
  "detail": "Внутренняя ошибка сервера",
  "error_code": "INTERNAL_ERROR"
}
```

---

## Реализация эндпоинта

```python
# api/endpoints/recommend.py

from fastapi import APIRouter, Depends, HTTPException

from api.schemas import RecommendRequest, RecommendResponse, ErrorResponse
from services.recommendation import RecommendationService, get_recommendation_service
from services.exceptions import LLMError, LLMParseError

router = APIRouter(tags=["recommendations"])


@router.post(
  "/recommend",
  response_model=RecommendResponse,
  responses={
    502: {"model": ErrorResponse},
    500: {"model": ErrorResponse},
  },
  summary="Рекомендация по обновлению смартфона",
)
async def recommend(
  request: RecommendRequest,
  service: RecommendationService = Depends(get_recommendation_service),
) -> RecommendResponse:
  try:
    return await service.recommend(request)
  except LLMParseError as e:
    raise HTTPException(status_code=502, detail=str(e)) from e
  except LLMError as e:
    raise HTTPException(status_code=502, detail=str(e)) from e
  except Exception as e:
    raise HTTPException(
      status_code=500,
      detail="Внутренняя ошибка сервера",
    ) from e
```

```python
# api/router.py

from fastapi import APIRouter
from api.endpoints import recommend

api_router = APIRouter()
api_router.include_router(recommend.router)
```

```python
# main.py

from fastapi import FastAPI
from api.router import api_router

app = FastAPI(
  title="Phone Recommendation API",
  description="Рекомендации по обновлению смартфона на базе LLM",
  version="1.0.0",
)
app.include_router(api_router)
```

---

## Health-check (опционально)

Для мониторинга и Docker:

### `GET /health`

```json
{
  "status": "ok"
}
```

Не вызывает OpenAI — только проверяет, что процесс API жив.
