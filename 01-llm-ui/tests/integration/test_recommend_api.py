import pytest
from unittest.mock import AsyncMock

from api.schemas import RecommendResponse, UpgradeUrgency, UsageProfile
from main import app
from services.recommendation import get_recommendation_service


@pytest.mark.asyncio
async def test_recommend_success(client):
    mock_response = RecommendResponse(
        upgrade_needed=True,
        urgency=UpgradeUrgency.RECOMMENDED,
        summary="Тест.",
        current_phone_assessment="Тест.",
        recommendations=[],
        usage_profile=UsageProfile.GAMING,
        current_phone="iPhone 12",
    )

    mock_service = AsyncMock()
    mock_service.recommend.return_value = mock_response
    app.dependency_overrides[get_recommendation_service] = lambda: mock_service

    try:
        response = await client.post(
            "/recommend",
            json={"current_phone": "iPhone 12", "usage_profile": "gaming"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["upgrade_needed"] is True


@pytest.mark.asyncio
async def test_recommend_validation_error(client):
    response = await client.post(
        "/recommend",
        json={"current_phone": " ", "usage_profile": "gaming"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_health(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
