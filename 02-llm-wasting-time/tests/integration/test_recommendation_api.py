"""
Интеграционные тесты HTTP API — рекомендации и история.

Спецификация: docs/api.md, docs/validation.md
"""

from unittest.mock import AsyncMock

import pytest

from api.schemas import (
    ClarificationResponse,
    RecommendationResponse,
    RecommendationStatus,
)
from main import app
from services.recommendation_service import get_recommendation_service


@pytest.fixture
def mock_recommendation_service():
    return AsyncMock()


class TestRecommendationAPI:
    @pytest.mark.asyncio
    async def test_post_recommendation_returns_clarification(
        self, client, mock_recommendation_service, sample_user_query
    ):
        mock_recommendation_service.start_recommendation.return_value = ClarificationResponse(
            session_id=1,
            questions=[],
            message="Уточним детали",
        )
        app.dependency_overrides[get_recommendation_service] = lambda: mock_recommendation_service
        try:
            response = await client.post(
                "/recommendation",
                json={"user_query": sample_user_query},
            )
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 200
        assert response.json()["status"] == "needs_clarification"

    @pytest.mark.asyncio
    async def test_post_recommendation_returns_completed(
        self, client, mock_recommendation_service, sample_user_query, fixed_datetime
    ):
        mock_recommendation_service.start_recommendation.return_value = RecommendationResponse(
            recommendation_id=1,
            session_id=1,
            user_query=sample_user_query,
            main_recommendation="Прогулка по парку Горького с другом.",
            alternatives=[],
            reasoning="Подходит под бюджет и компанию.",
            budget_estimation="2000 ₽",
            time_estimation="4 часа",
            created_at=fixed_datetime,
        )
        app.dependency_overrides[get_recommendation_service] = lambda: mock_recommendation_service
        try:
            response = await client.post(
                "/recommendation",
                json={"user_query": sample_user_query},
            )
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 200
        assert response.json()["status"] == "completed"

    @pytest.mark.asyncio
    async def test_post_recommendation_validation_error_short_query(self, client):
        response = await client.post("/recommendation", json={"user_query": "да"})
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_post_recommendation_profile_not_found(
        self, client, mock_recommendation_service, sample_user_query
    ):
        from services.exceptions import ProfileNotFoundError

        mock_recommendation_service.start_recommendation.side_effect = ProfileNotFoundError(
            "Профиль не найден"
        )
        app.dependency_overrides[get_recommendation_service] = lambda: mock_recommendation_service
        try:
            response = await client.post(
                "/recommendation",
                json={"user_query": sample_user_query, "profile_id": 999},
            )
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 404
        assert response.json()["error_code"] == "PROFILE_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_post_continue_success(
        self, client, mock_recommendation_service, sample_user_query, fixed_datetime, sample_continue_answers
    ):
        mock_recommendation_service.continue_recommendation.return_value = RecommendationResponse(
            recommendation_id=1,
            session_id=1,
            user_query=sample_user_query,
            main_recommendation="Прогулка по парку.",
            alternatives=[],
            reasoning="Причина.",
            budget_estimation="2000 ₽",
            time_estimation="4 часа",
            created_at=fixed_datetime,
        )
        app.dependency_overrides[get_recommendation_service] = lambda: mock_recommendation_service
        try:
            response = await client.post(
                "/recommendation/continue",
                json={"session_id": 1, "answers": sample_continue_answers},
            )
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 200
        assert response.json()["status"] == "completed"

    @pytest.mark.asyncio
    async def test_post_continue_session_not_found(self, client, mock_recommendation_service, sample_continue_answers):
        from services.exceptions import SessionNotFoundError

        mock_recommendation_service.continue_recommendation.side_effect = SessionNotFoundError(
            "Сессия не найдена"
        )
        app.dependency_overrides[get_recommendation_service] = lambda: mock_recommendation_service
        try:
            response = await client.post(
                "/recommendation/continue",
                json={"session_id": 999, "answers": sample_continue_answers},
            )
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_post_continue_session_invalid_state(
        self, client, mock_recommendation_service, sample_continue_answers
    ):
        from services.exceptions import SessionInvalidStateError

        mock_recommendation_service.continue_recommendation.side_effect = SessionInvalidStateError(
            "Сессия не ожидает ответов"
        )
        app.dependency_overrides[get_recommendation_service] = lambda: mock_recommendation_service
        try:
            response = await client.post(
                "/recommendation/continue",
                json={"session_id": 1, "answers": sample_continue_answers},
            )
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_post_continue_session_expired(
        self, client, mock_recommendation_service, sample_continue_answers
    ):
        from services.exceptions import SessionExpiredError

        mock_recommendation_service.continue_recommendation.side_effect = SessionExpiredError(
            "Сессия истекла"
        )
        app.dependency_overrides[get_recommendation_service] = lambda: mock_recommendation_service
        try:
            response = await client.post(
                "/recommendation/continue",
                json={"session_id": 1, "answers": sample_continue_answers},
            )
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 410

    @pytest.mark.asyncio
    async def test_get_history(self, client, mock_recommendation_service, sample_user_query, fixed_datetime):
        from api.schemas import HistoryItem, HistoryResponse

        mock_recommendation_service.get_history.return_value = HistoryResponse(
            items=[
                HistoryItem(
                    id=1,
                    user_query=sample_user_query,
                    main_recommendation="Прогулка.",
                    budget_estimation="2000 ₽",
                    time_estimation="4 ч",
                    created_at=fixed_datetime,
                    has_feedback=False,
                )
            ],
            total=1,
            limit=20,
            offset=0,
        )
        app.dependency_overrides[get_recommendation_service] = lambda: mock_recommendation_service
        try:
            response = await client.get("/history")
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 200
        assert response.json()["total"] == 1

    @pytest.mark.asyncio
    async def test_get_history_detail(self, client, mock_recommendation_service, fixed_datetime):
        from api.schemas import HistoryDetailResponse

        mock_recommendation_service.get_history_detail.return_value = HistoryDetailResponse(
            id=1,
            session_id=1,
            user_query="Запрос",
            context={"budget": "5000"},
            main_recommendation="Прогулка.",
            alternatives=[],
            reasoning="Причина.",
            budget_estimation="2000 ₽",
            time_estimation="4 ч",
            created_at=fixed_datetime,
            feedback=None,
        )
        app.dependency_overrides[get_recommendation_service] = lambda: mock_recommendation_service
        try:
            response = await client.get("/history/1")
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 200
        assert response.json()["id"] == 1

    @pytest.mark.asyncio
    async def test_llm_error_returns_502(self, client, mock_recommendation_service, sample_user_query):
        from services.exceptions import LLMParseError

        mock_recommendation_service.start_recommendation.side_effect = LLMParseError(
            "Невалидный JSON"
        )
        app.dependency_overrides[get_recommendation_service] = lambda: mock_recommendation_service
        try:
            response = await client.post(
                "/recommendation",
                json={"user_query": sample_user_query},
            )
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 502
        assert response.json()["error_code"] == "LLM_PARSE_ERROR"
