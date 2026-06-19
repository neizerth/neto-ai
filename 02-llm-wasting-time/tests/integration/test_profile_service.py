"""
Интеграционные тесты ProfileService.

Спецификация: docs/models.md, docs/validation.md
"""

import pytest

from api.schemas import ActivityLevel, BudgetRange, ProfileUpsertRequest
from services.exceptions import ProfileNotFoundError
from services.profile_service import ProfileService


@pytest.fixture
def profile_service():
    return ProfileService()


class TestProfileService:
    @pytest.mark.asyncio
    async def test_upsert_creates_profile(self, profile_service, sample_profile_payload):
        request = ProfileUpsertRequest(**sample_profile_payload)
        profile = await profile_service.upsert_profile(request)

        assert profile.id >= 1
        assert profile.budget == BudgetRange.MEDIUM
        assert profile.activity_level == ActivityLevel.MODERATE
        assert "кино" in profile.favorite_activities

    @pytest.mark.asyncio
    async def test_upsert_updates_existing_profile(self, profile_service, sample_profile_payload):
        request = ProfileUpsertRequest(**sample_profile_payload)
        created = await profile_service.upsert_profile(request)

        updated_request = ProfileUpsertRequest(
            budget="high",
            activity_level="high",
            favorite_activities=["спорт"],
            disliked_activities=[],
        )
        updated = await profile_service.upsert_profile(updated_request)

        assert updated.id == created.id
        assert updated.budget == BudgetRange.HIGH
        assert updated.favorite_activities == ["спорт"]

    @pytest.mark.asyncio
    async def test_get_profile_returns_saved_profile(
        self, profile_service, sample_profile_payload
    ):
        await profile_service.upsert_profile(ProfileUpsertRequest(**sample_profile_payload))
        profile = await profile_service.get_profile()

        assert profile.budget == BudgetRange.MEDIUM
        assert profile.updated_at >= profile.created_at

    @pytest.mark.asyncio
    async def test_get_profile_raises_when_not_exists(self, profile_service):
        with pytest.raises(ProfileNotFoundError):
            await profile_service.get_profile()

    @pytest.mark.asyncio
    async def test_upsert_removes_overlap_between_favorite_and_disliked(
        self, profile_service
    ):
        request = ProfileUpsertRequest(
            favorite_activities=["кино", "клубы"],
            disliked_activities=["клубы"],
        )
        profile = await profile_service.upsert_profile(request)
        assert "клубы" not in profile.favorite_activities
        assert "клубы" in profile.disliked_activities
