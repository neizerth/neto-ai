import asyncio

from openai import APIConnectionError, APITimeoutError, AsyncOpenAI, RateLimitError

from config.settings import Settings
from llm.prompts import SYSTEM_PROMPT
from services.exceptions import LLMError


class OpenAIClient:
    def __init__(self, settings: Settings):
        self._client = AsyncOpenAI(
            api_key=settings.openai_api_key,
            timeout=settings.openai_timeout_seconds,
        )
        self._model = settings.openai_model
        self._temperature = settings.openai_temperature

    async def get_recommendation_json(self, user_prompt: str) -> str:
        for attempt in range(2):
            try:
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
            except (APITimeoutError, APIConnectionError) as e:
                raise LLMError("Не удалось получить ответ от модели") from e
            except RateLimitError:
                if attempt == 0:
                    await asyncio.sleep(1)
                    continue
                raise LLMError("Превышен лимит запросов к модели") from None
            except LLMError:
                raise
            except Exception as e:
                raise LLMError("Ошибка при обращении к модели") from e

        raise LLMError("Превышен лимит запросов к модели")
