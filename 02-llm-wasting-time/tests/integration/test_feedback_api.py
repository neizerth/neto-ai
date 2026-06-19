"""
Интеграционные тесты HTTP API — обратная связь и health.

Спецификация: docs/api.md
"""

from unittest.mock import AsyncMock

import pytest

from api.schemas import FeedbackResponse
from main import app
from services.feedback_service import get_feedback_service


@pytest.fixture
def mock_feedback_service():
    return AsyncMock()


class TestFeedbackAPI:
    @pytest.mark.asyncio
    async def test_post_feedback_created(
        self, client, mock_feedback_service, sample_feedback_payload, fixed_datetime
    ):
        mock_feedback_service.create_feedback.return_value = FeedbackResponse(
            id=1,
            recommendation_id=1,
            rating=5,
            comment="Отлично!",
            created_at=fixed_datetime,
        )
        app.dependency_overrides[get_feedback_service] = lambda: mock_feedback_service
        try:
            response = await client.post("/feedback", json=sample_feedback_payload)
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 201
        assert response.json()["rating"] == 5

    @pytest.mark.asyncio
    async def test_post_feedback_not_found(self, client, mock_feedback_service, sample_feedback_payload):
        from services.exceptions import RecommendationNotFoundError

        mock_feedback_service.create_feedback.side_effect = RecommendationNotFoundError("Нет")
        app.dependency_overrides[get_feedback_service] = lambda: mock_feedback_service
        try:
            response = await client.post("/feedback", json=sample_feedback_payload)
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_post_feedback_duplicate(self, client, mock_feedback_service, sample_feedback_payload):
        from services.exceptions import FeedbackAlreadyExistsError

        mock_feedback_service.create_feedback.side_effect = FeedbackAlreadyExistsError("Уже есть")
        app.dependency_overrides[get_feedback_service] = lambda: mock_feedback_service
        try:
            response = await client.post("/feedback", json=sample_feedback_payload)
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_post_feedback_invalid_rating(self, client):
        response = await client.post(
            "/feedback",
            json={"recommendation_id": 1, "rating": 10},
        )
        assert response.status_code == 422


class TestHealthAPI:
    @pytest.mark.asyncio
    async def test_health_ok(self, client):
        response = await client.get("/health")
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "ok"
        assert body.get("database") == "ok"
