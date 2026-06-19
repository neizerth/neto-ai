"""
Интеграционные тесты FeedbackService.

Спецификация: docs/validation.md
"""

import pytest

from api.schemas import FeedbackCreateRequest, RecommendationStartRequest
from llm.schemas import ClarificationPayload, RecommendationPayload
from services.exceptions import FeedbackAlreadyExistsError, RecommendationNotFoundError
from services.feedback_service import FeedbackService
from services.recommendation_service import RecommendationService


@pytest.fixture
def feedback_service():
    return FeedbackService()


@pytest.fixture
def recommendation_service(mock_llm_provider):
    return RecommendationService(llm_provider=mock_llm_provider)


async def _create_recommendation(recommendation_service, mock_llm_provider, sample_user_query, sample_recommendation_payload):
    mock_llm_provider.generate_clarification.return_value = ClarificationPayload(
        needs_clarification=False, questions=[], extracted_context={}
    )
    mock_llm_provider.generate_recommendation.return_value = RecommendationPayload(
        **sample_recommendation_payload
    )
    return await recommendation_service.start_recommendation(
        RecommendationStartRequest(user_query=sample_user_query)
    )


class TestFeedbackService:
    @pytest.mark.asyncio
    async def test_create_feedback_success(
        self,
        feedback_service,
        recommendation_service,
        mock_llm_provider,
        sample_user_query,
        sample_recommendation_payload,
        sample_feedback_payload,
    ):
        rec = await _create_recommendation(
            recommendation_service, mock_llm_provider, sample_user_query, sample_recommendation_payload
        )
        payload = {**sample_feedback_payload, "recommendation_id": rec.recommendation_id}
        feedback = await feedback_service.create_feedback(FeedbackCreateRequest(**payload))

        assert feedback.id >= 1
        assert feedback.rating == 5
        assert feedback.recommendation_id == rec.recommendation_id

    @pytest.mark.asyncio
    async def test_create_feedback_raises_when_recommendation_not_found(
        self, feedback_service, sample_feedback_payload
    ):
        with pytest.raises(RecommendationNotFoundError):
            await feedback_service.create_feedback(
                FeedbackCreateRequest(**sample_feedback_payload)
            )

    @pytest.mark.asyncio
    async def test_create_feedback_raises_on_duplicate(
        self,
        feedback_service,
        recommendation_service,
        mock_llm_provider,
        sample_user_query,
        sample_recommendation_payload,
        sample_feedback_payload,
    ):
        rec = await _create_recommendation(
            recommendation_service, mock_llm_provider, sample_user_query, sample_recommendation_payload
        )
        payload = {**sample_feedback_payload, "recommendation_id": rec.recommendation_id}
        await feedback_service.create_feedback(FeedbackCreateRequest(**payload))

        with pytest.raises(FeedbackAlreadyExistsError):
            await feedback_service.create_feedback(FeedbackCreateRequest(**payload))

    @pytest.mark.asyncio
    async def test_create_feedback_without_comment(
        self,
        feedback_service,
        recommendation_service,
        mock_llm_provider,
        sample_user_query,
        sample_recommendation_payload,
    ):
        rec = await _create_recommendation(
            recommendation_service, mock_llm_provider, sample_user_query, sample_recommendation_payload
        )
        feedback = await feedback_service.create_feedback(
            FeedbackCreateRequest(recommendation_id=rec.recommendation_id, rating=4)
        )
        assert feedback.comment is None
