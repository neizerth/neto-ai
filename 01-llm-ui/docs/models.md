# Модели и типы данных

Все модели — **Pydantic v2**. Размещаются в `api/schemas.py` (или `models/schemas.py` при росте проекта).

## Enum-типы

### `UsageProfile` — сценарий использования

Определяет, для каких задач пользователь использует телефон. Влияет на критерии оценки (камера, GPU, автономность и т.д.).

```python
from enum import Enum


class UsageProfile(str, Enum):
  EVERYDAY = "everyday"           # Повседневное использование
  GAMING = "gaming"               # Игры
  PHOTOGRAPHY = "photography"     # Фотография (любительская)
  PRO_PHOTOGRAPHY = "pro_photography"  # Профессиональная фотография
  VIDEO_CREATION = "video_creation"    # Съёмка и монтаж видео
  BUSINESS = "business"           # Деловое использование
  BATTERY_LIFE = "battery_life"   # Приоритет — автономность
  COMPACT = "compact"             # Компактность и удобство
```

**Отображение в UI (русский):**

| Значение | Подпись |
|----------|---------|
| `everyday` | Повседневное использование |
| `gaming` | Игры |
| `photography` | Фотография |
| `pro_photography` | Профессиональная фотография |
| `video_creation` | Видеосъёмка и монтаж |
| `business` | Деловое использование |
| `battery_life` | Долгая автономность |
| `compact` | Компактный размер |

### `UpgradeUrgency` — срочность обновления (в ответе)

```python
class UpgradeUrgency(str, Enum):
  NOT_NEEDED = "not_needed"   # Обновление не требуется
  OPTIONAL = "optional"       # Можно обновить, но не обязательно
  RECOMMENDED = "recommended" # Рекомендуется обновить
  URGENT = "urgent"           # Сильно устарело для сценария
```

---

## Входные модели

### `RecommendRequest`

```python
from pydantic import BaseModel, Field, field_validator
import re


class RecommendRequest(BaseModel):
  current_phone: str = Field(
    ...,
    min_length=2,
    max_length=100,
    description="Текущая модель телефона, например: iPhone 12, Samsung Galaxy S21",
    examples=["iPhone 12", "Samsung Galaxy S21 Ultra"],
  )
  usage_profile: UsageProfile = Field(
    ...,
    description="Основной сценарий использования",
  )
  additional_requirements: str | None = Field(
    default=None,
    max_length=500,
    description="Дополнительные пожелания: бюджет, бренд, размер экрана",
  )
  max_recommendations: int = Field(
    default=3,
    ge=1,
    le=5,
    description="Максимальное число рекомендуемых моделей",
  )

  @field_validator("current_phone")
  @classmethod
  def normalize_phone_name(cls, v: str) -> str:
    v = v.strip()
    if not v:
      raise ValueError("Название модели не может быть пустым")
    # Убираем лишние пробелы
    v = re.sub(r"\s+", " ", v)
    return v

  @field_validator("additional_requirements")
  @classmethod
  def strip_requirements(cls, v: str | None) -> str | None:
    if v is None:
      return None
    v = v.strip()
    return v or None
```

### Правила валидации входа

| Поле | Правило | Сообщение об ошибке |
|------|---------|---------------------|
| `current_phone` | 2–100 символов, не пустое после trim | «Название модели не может быть пустым» |
| `usage_profile` | Одно из значений enum | Стандартное Pydantic |
| `additional_requirements` | ≤ 500 символов | «Не более 500 символов» |
| `max_recommendations` | 1–5 | «Допустимый диапазон: 1–5» |

---

## Промежуточные модели (ответ LLM)

Схема, которую LLM обязана вернуть в JSON. Используется для парсинга и валидации сырого ответа.

### `LLMPhoneRecommendation`

```python
class LLMPhoneRecommendation(BaseModel):
  brand: str = Field(..., min_length=1, max_length=50)
  model: str = Field(..., min_length=1, max_length=100)
  full_name: str = Field(..., min_length=2, max_length=150)
  reason: str = Field(..., min_length=10, max_length=500)
  estimated_price_range: str | None = Field(
    default=None,
    max_length=100,
    description="Примерный ценовой диапазон, например: 80 000–100 000 ₽",
  )
```

### `LLMRecommendationPayload`

```python
class LLMRecommendationPayload(BaseModel):
  upgrade_needed: bool
  urgency: UpgradeUrgency
  summary: str = Field(..., min_length=10, max_length=1000)
  current_phone_assessment: str = Field(..., min_length=10, max_length=500)
  recommendations: list[LLMPhoneRecommendation] = Field(default_factory=list)

  @field_validator("recommendations")
  @classmethod
  def validate_recommendations_consistency(
    cls, v: list[LLMPhoneRecommendation], info
  ) -> list[LLMPhoneRecommendation]:
    upgrade_needed = info.data.get("upgrade_needed")
    urgency = info.data.get("urgency")

    if not upgrade_needed and v:
      raise ValueError(
        "Если upgrade_needed=false, список recommendations должен быть пустым"
      )
    if upgrade_needed and urgency == UpgradeUrgency.NOT_NEEDED:
      raise ValueError("upgrade_needed=true несовместимо с urgency=not_needed")
    if not upgrade_needed and urgency != UpgradeUrgency.NOT_NEEDED:
      raise ValueError("При upgrade_needed=false urgency должен быть not_needed")
    return v
```

---

## Выходные модели (API-ответ)

### `PhoneRecommendation`

```python
class PhoneRecommendation(BaseModel):
  brand: str
  model: str
  full_name: str
  reason: str
  estimated_price_range: str | None = None
```

### `RecommendResponse`

```python
class RecommendResponse(BaseModel):
  upgrade_needed: bool
  urgency: UpgradeUrgency
  summary: str
  current_phone_assessment: str
  recommendations: list[PhoneRecommendation]
  usage_profile: UsageProfile          # эхо входного значения
  current_phone: str                   # эхо входного значения
```

### `ErrorResponse`

```python
class ErrorResponse(BaseModel):
  detail: str
  error_code: str | None = None
```

---

## Маппинг LLM → API

```python
def to_api_response(
  payload: LLMRecommendationPayload,
  request: RecommendRequest,
) -> RecommendResponse:
  return RecommendResponse(
    upgrade_needed=payload.upgrade_needed,
    urgency=payload.urgency,
    summary=payload.summary,
    current_phone_assessment=payload.current_phone_assessment,
    recommendations=[
      PhoneRecommendation(**rec.model_dump())
      for rec in payload.recommendations
    ],
    usage_profile=request.usage_profile,
    current_phone=request.current_phone,
  )
```

---

## JSON Schema для OpenAI

Передайте схему `LLMRecommendationPayload` в `response_format` (structured outputs) или включите её текстом в system-промпт при `json_object` mode.

Ключевые ограничения для промпта:

- `recommendations` — массив длиной `0` при `upgrade_needed: false`.
- `recommendations` — не более `max_recommendations` из запроса.
- `urgency` — одно из: `not_needed`, `optional`, `recommended`, `urgent`.
