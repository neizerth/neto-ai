"""
Интеграционные тесты HTTP API — профиль.

Спецификация: docs/api.md
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest

from api.schemas import ActivityLevel, BudgetRange, ProfileResponse
from main import app
from services.profile_service import get_profile_service


@pytest.fixture
def mock_profile_service():
    return AsyncMock()


@pytest.fixture
def sample_profile_response(fixed_datetime):
    return ProfileResponse(
        id=1,
        budget=BudgetRange.MEDIUM,
        activity_level=ActivityLevel.MODERATE,
        favorite_activities=["кино"],
        disliked_activities=["клубы"],
        created_at=fixed_datetime,
        updated_at=fixed_datetime,
    )


class TestProfileAPI:
    @pytest.mark.asyncio
    async def test_get_profile_success(
        self, client, mock_profile_service, sample_profile_response
    ):
        mock_profile_service.get_profile.return_value = sample_profile_response
        app.dependency_overrides[get_profile_service] = lambda: mock_profile_service
        try:
            response = await client.get("/profile")
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 200
        assert response.json()["budget"] == "medium"

    @pytest.mark.asyncio
    async def test_get_profile_not_found(self, client, mock_profile_service):
        from services.exceptions import ProfileNotFoundError

        mock_profile_service.get_profile.side_effect = ProfileNotFoundError("Не найден")
        app.dependency_overrides[get_profile_service] = lambda: mock_profile_service
        try:
            response = await client.get("/profile")
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_put_profile_upsert(
        self, client, mock_profile_service, sample_profile_response, sample_profile_payload
    ):
        mock_profile_service.upsert_profile.return_value = sample_profile_response
        app.dependency_overrides[get_profile_service] = lambda: mock_profile_service
        try:
            response = await client.put("/profile", json=sample_profile_payload)
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 200
        assert response.json()["id"] == 1
