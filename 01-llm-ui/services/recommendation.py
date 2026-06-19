from functools import lru_cache

from api.schemas import RecommendRequest, RecommendResponse, to_api_response
from config.settings import get_settings
from llm.client import OpenAIClient
from llm.parser import parse_llm_response
from llm.prompts import build_user_prompt
from services.exceptions import LLMParseError


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
        payload.recommendations = payload.recommendations[: request.max_recommendations]

        if payload.upgrade_needed and not payload.recommendations:
            raise LLMParseError(
                "Модель не вернула рекомендации при upgrade_needed=true"
            )

        return to_api_response(payload, request)


@lru_cache
def _get_llm_client() -> OpenAIClient:
    return OpenAIClient(get_settings())


def get_recommendation_service() -> RecommendationService:
    return RecommendationService(_get_llm_client())
