import pytest
from pydantic import ValidationError

from api.schemas import LLMRecommendationPayload, RecommendRequest, UsageProfile


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
    payload = LLMRecommendationPayload.model_validate(
        {
            "upgrade_needed": False,
            "urgency": "not_needed",
            "summary": "Телефон отлично подходит.",
            "current_phone_assessment": "Флагман 2023 года.",
            "recommendations": [],
        }
    )
    assert not payload.upgrade_needed


def test_upgrade_not_needed_with_recommendations_fails():
    with pytest.raises(ValidationError):
        LLMRecommendationPayload.model_validate(
            {
                "upgrade_needed": False,
                "urgency": "not_needed",
                "summary": "Тест.",
                "current_phone_assessment": "Тест.",
                "recommendations": [
                    {
                        "brand": "A",
                        "model": "B",
                        "full_name": "A B",
                        "reason": "x" * 10,
                    }
                ],
            }
        )
