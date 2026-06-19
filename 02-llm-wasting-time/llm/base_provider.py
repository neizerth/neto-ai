from llm import prompts
from llm.schemas import ClarificationPayload, RecommendationPayload


class BaseLLMProvider:
    async def generate_clarification(
        self, user_query: str, profile: dict | None
    ) -> ClarificationPayload:
        raise NotImplementedError

    async def generate_recommendation(
        self, user_query: str, context: dict[str, str], profile: dict | None
    ) -> RecommendationPayload:
        raise NotImplementedError


def _to_clarification(data) -> ClarificationPayload:
    if isinstance(data, ClarificationPayload):
        return data
    return ClarificationPayload.model_validate(data)


def _to_recommendation(data) -> RecommendationPayload:
    if isinstance(data, RecommendationPayload):
        return data
    return RecommendationPayload.model_validate(data)
