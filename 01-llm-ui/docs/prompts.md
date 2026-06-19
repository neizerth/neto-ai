# Промпты и работа с LLM

## Стратегия

1. **System prompt** — роль, правила, формат JSON, критерии оценки по профилям.
2. **User prompt** — конкретные данные запроса (телефон, профиль, пожелания).
3. **Response format** — `response_format={"type": "json_object"}` (OpenAI Chat Completions).
4. **Парсинг** — `LLMRecommendationPayload.model_validate_json()`.

Рекомендуемая модель: `gpt-4o-mini` (баланс цена/качество). Для более точных оценок — `gpt-4o`.

Параметры вызова:

| Параметр | Значение | Обоснование |
|----------|----------|-------------|
| `temperature` | `0.3` | Стабильные, воспроизводимые рекомендации |
| `max_tokens` | `1500` | Достаточно для 3–5 рекомендаций с обоснованием |
| `timeout` | `30s` | Защита от зависания |

---

## System prompt

```text
Ты — эксперт по смартфонам и мобильным устройствам. Твоя задача — оценить, нужно ли пользователю обновить текущий телефон, исходя из модели устройства и сценария использования.

Правила:
1. Отвечай ТОЛЬКО валидным JSON без markdown-обёрток и пояснений вне JSON.
2. Рекомендуй только реально существующие модели смартфонов, доступные на рынке на момент 2025–2026 года.
3. Если текущий телефон достаточен для сценария — честно скажи, что обновление не требуется (upgrade_needed: false).
4. Не выдумывай характеристики. Если не уверен в модели — не включай её в рекомендации.
5. Учитывай возраст устройства, производительность, камеру, автономность, экран, поддержку обновлений ОС.
6. Количество рекомендаций — не более указанного в запросе max_recommendations.
7. Если upgrade_needed=false, массив recommendations должен быть пустым [], urgency="not_needed".
8. Пиши на русском языке (поля reason, summary, current_phone_assessment).
9. Ценовые диапазоны указывай в рублях (₽), ориентировочно.

Критерии по сценариям:
- everyday: баланс цена/качество, плавность UI, базовая камера, автономность
- gaming: GPU, охлаждение, частота экрана, объём RAM
- photography: качество основной камеры, ночная съёмка, ультраширик
- pro_photography: RAW/ProRes, зум, стабилизация, цветопередача, pro-приложения
- video_creation: стабилизация, кодеки, 4K/8K, микрофоны, хранилище
- business: безопасность, автономность, надёжность, экосистема
- battery_life: ёмкость батареи, энергоэффективность чипа
- compact: габариты, вес, удобство одной руки

Формат ответа (строго):
{
  "upgrade_needed": boolean,
  "urgency": "not_needed" | "optional" | "recommended" | "urgent",
  "summary": "string — общий вывод в 2–4 предложениях",
  "current_phone_assessment": "string — оценка текущего телефона",
  "recommendations": [
    {
      "brand": "string",
      "model": "string",
      "full_name": "string",
      "reason": "string — почему подходит под сценарий",
      "estimated_price_range": "string | null"
    }
  ]
}
```

---

## User prompt (шаблон)

```python
# llm/prompts.py

USAGE_PROFILE_LABELS = {
  "everyday": "Повседневное использование",
  "gaming": "Игры",
  "photography": "Фотография",
  "pro_photography": "Профессиональная фотография",
  "video_creation": "Видеосъёмка и монтаж",
  "business": "Деловое использование",
  "battery_life": "Долгая автономность",
  "compact": "Компактный размер",
}

USER_PROMPT_TEMPLATE = """Проанализируй необходимость обновления смартфона.

Текущий телефон: {current_phone}
Сценарий использования: {usage_profile_label} ({usage_profile})
Максимум рекомендаций: {max_recommendations}
{additional_block}

Верни JSON строго по указанной схеме."""


def build_user_prompt(
  current_phone: str,
  usage_profile: str,
  max_recommendations: int,
  additional_requirements: str | None = None,
) -> str:
  additional_block = ""
  if additional_requirements:
    additional_block = f"Дополнительные пожелания: {additional_requirements}"

  return USER_PROMPT_TEMPLATE.format(
    current_phone=current_phone,
    usage_profile=usage_profile,
    usage_profile_label=USAGE_PROFILE_LABELS.get(usage_profile, usage_profile),
    max_recommendations=max_recommendations,
    additional_block=additional_block,
  )
```

---

## Клиент OpenAI

```python
# llm/client.py

from openai import AsyncOpenAI
from config.settings import Settings

SYSTEM_PROMPT = "..."  # текст выше


class OpenAIClient:
  def __init__(self, settings: Settings):
    self._client = AsyncOpenAI(
      api_key=settings.openai_api_key,
      timeout=settings.openai_timeout_seconds,
    )
    self._model = settings.openai_model
    self._temperature = settings.openai_temperature

  async def get_recommendation_json(
    self,
    user_prompt: str,
  ) -> str:
    response = await self._client.chat.completions.create(
      model=self._model,
      temperature=self._temperature,
      max_tokens=1500,
      response_format={"type": "json_object"},
      messages=[
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
      ],
    )
    content = response.choices[0].message.content
    if not content:
      raise LLMError("Пустой ответ от модели")
    return content
```

---

## Парсер ответа

```python
# llm/parser.py

from pydantic import ValidationError
from api.schemas import LLMRecommendationPayload


class LLMParseError(Exception):
  pass


def parse_llm_response(raw_json: str) -> LLMRecommendationPayload:
  try:
    payload = LLMRecommendationPayload.model_validate_json(raw_json)
  except ValidationError as e:
    raise LLMParseError(f"Невалидный JSON от LLM: {e}") from e

  return payload
```

---

## Постобработка в сервисе

После парсинга `RecommendationService` дополнительно:

1. Обрезает `recommendations` до `request.max_recommendations` (на случай нарушения лимита LLM).
2. Маппит в `RecommendResponse`.

```python
# services/recommendation.py

class RecommendationService:
  def __init__(self, llm_client: OpenAIClient):
    self._llm = llm_client

  async def recommend(self, request: RecommendRequest) -> RecommendResponse:
    user_prompt = build_user_prompt(
      current_phone=request.current_phone,
      usage_profile=request.usage_profile.value,
      max_recommendations=request.max_recommendations,
      additional_requirements=request.additional_requirements,
    )

    raw = await self._llm.get_recommendation_json(user_prompt)
    payload = parse_llm_response(raw)

    # Страховка: обрезать лишние рекомендации
    payload.recommendations = payload.recommendations[: request.max_recommendations]

    return to_api_response(payload, request)
```

---

## Обработка edge-cases

| Ситуация | Поведение |
|----------|-----------|
| LLM вернула markdown ` ```json ... ``` ` | Очистить обёртку перед парсингом |
| Неизвестная модель телефона | LLM должна оценить по названию; в summary указать допущения |
| `upgrade_needed=true`, пустой `recommendations` | `502` — нарушение контракта |
| Таймаут OpenAI | `502` с `error_code: LLM_TIMEOUT` |
| Rate limit | Retry 1 раз с backoff; затем `502` |

### Очистка markdown (опционально)

```python
import re

def strip_markdown_json(text: str) -> str:
  text = text.strip()
  match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
  return match.group(1).strip() if match else text
```
