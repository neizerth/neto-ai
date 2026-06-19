import re

from pydantic import ValidationError

from api.schemas import LLMRecommendationPayload
from services.exceptions import LLMParseError


def strip_markdown_json(text: str) -> str:
    text = text.strip()
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    return match.group(1).strip() if match else text


def parse_llm_response(raw_json: str) -> LLMRecommendationPayload:
    cleaned = strip_markdown_json(raw_json)
    try:
        return LLMRecommendationPayload.model_validate_json(cleaned)
    except ValidationError as e:
        raise LLMParseError(f"Невалидный JSON от LLM: {e}") from e
