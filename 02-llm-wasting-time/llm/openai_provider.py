import json

from openai import AsyncOpenAI

from config.settings import Settings
from llm.base_provider import BaseLLMProvider, _to_clarification, _to_recommendation
from llm import prompts
from llm.schemas import ClarificationPayload, RecommendationPayload
from services.exceptions import LLMError, LLMParseError


class OpenAIProvider(BaseLLMProvider):
    def __init__(self, settings: Settings):
        self._client = AsyncOpenAI(
            api_key=settings.openai_api_key,
            timeout=settings.openai_timeout_seconds,
        )
        self._model = settings.model_name

    async def _call_json(self, system: str, user: str) -> dict:
        try:
            response = await self._client.chat.completions.create(
                model=self._model,
                temperature=0.3,
                max_tokens=2000,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            )
            content = response.choices[0].message.content
            if not content:
                raise LLMError("Пустой ответ от модели")
            return json.loads(content)
        except LLMParseError:
            raise
        except json.JSONDecodeError as e:
            raise LLMParseError("Не удалось получить корректный ответ от модели") from e
        except Exception as e:
            raise LLMError("Не удалось получить ответ от модели") from e

    async def generate_clarification(
        self, user_query: str, profile: dict | None
    ) -> ClarificationPayload:
        user_prompt = prompts.build_clarification_user_prompt(user_query, profile)
        system = f"{prompts.SYSTEM_PROMPT}\n{prompts.CLARIFICATION_PROMPT}"
        try:
            data = await self._call_json(system, user_prompt)
            return _to_clarification(data)
        except ValueError as e:
            raise LLMParseError(str(e)) from e

    async def generate_recommendation(
        self, user_query: str, context: dict[str, str], profile: dict | None
    ) -> RecommendationPayload:
        user_prompt = prompts.build_recommendation_user_prompt(user_query, context, profile)
        system = f"{prompts.SYSTEM_PROMPT}\n{prompts.RECOMMENDATION_PROMPT}"
        try:
            data = await self._call_json(system, user_prompt)
            return _to_recommendation(data)
        except ValueError as e:
            raise LLMParseError(str(e)) from e
