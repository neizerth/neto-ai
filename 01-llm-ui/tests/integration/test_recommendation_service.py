import pytest
from unittest.mock import AsyncMock

from services.recommendation import RecommendationService


@pytest.mark.asyncio
async def test_service_recommend(sample_request, valid_llm_json):
    mock_client = AsyncMock()
    mock_client.get_recommendation_json.return_value = valid_llm_json

    service = RecommendationService(mock_client)
    result = await service.recommend(sample_request)

    assert result.upgrade_needed is True
    assert result.current_phone == "iPhone 12"
    mock_client.get_recommendation_json.assert_called_once()


@pytest.mark.asyncio
async def test_service_trims_recommendations(sample_request, valid_llm_json):
    mock_client = AsyncMock()
    mock_client.get_recommendation_json.return_value = valid_llm_json

    sample_request.max_recommendations = 1
    service = RecommendationService(mock_client)
    result = await service.recommend(sample_request)

    assert len(result.recommendations) == 1
