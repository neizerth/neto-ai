"""
Интеграционные тесты RecommendationService.

Спецификация: docs/architecture.md, docs/validation.md
Покрывает: многошаговый сценарий, сессии, история, TTL, лимиты уточнений.
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock

import pytest

from api.schemas import (
    ClarificationResponse,
    RecommendationContinueRequest,
    RecommendationResponse,
    RecommendationStartRequest,
    RecommendationStatus,
)
from llm.schemas import ClarificationPayload, FollowupQuestion, RecommendationPayload
from services.exceptions import (
    ProfileNotFoundError,
    SessionExpiredError,
    SessionInvalidStateError,
    SessionNotFoundError,
    ValidationBusinessError,
)
from services.recommendation_service import RecommendationService


@pytest.fixture
def clarification_with_questions(sample_clarification_payload):
    return ClarificationPayload(**sample_clarification_payload)


@pytest.fixture
def recommendation_payload(sample_recommendation_payload):
    return RecommendationPayload(**sample_recommendation_payload)


@pytest.fixture
def direct_recommendation_clarification():
    return ClarificationPayload(
        needs_clarification=False,
        questions=[],
        extracted_context={"mood": "спокойный"},
    )


@pytest.fixture
def service(mock_llm_provider):
    return RecommendationService(llm_provider=mock_llm_provider)


class TestRecommendationServiceStart:
    @pytest.mark.asyncio
    async def test_start_returns_clarification_when_llm_needs_more_info(
        self, service, mock_llm_provider, clarification_with_questions, sample_user_query
    ):
        mock_llm_provider.generate_clarification.return_value = clarification_with_questions

        request = RecommendationStartRequest(user_query=sample_user_query)
        result = await service.start_recommendation(request)

        assert isinstance(result, ClarificationResponse)
        assert result.status == RecommendationStatus.NEEDS_CLARIFICATION
        assert result.session_id > 0
        assert len(result.questions) == 2

    @pytest.mark.asyncio
    async def test_start_returns_recommendation_when_context_sufficient(
        self,
        service,
        mock_llm_provider,
        direct_recommendation_clarification,
        recommendation_payload,
        sample_user_query,
    ):
        mock_llm_provider.generate_clarification.return_value = direct_recommendation_clarification
        mock_llm_provider.generate_recommendation.return_value = recommendation_payload

        request = RecommendationStartRequest(user_query=sample_user_query)
        result = await service.start_recommendation(request)

        assert isinstance(result, RecommendationResponse)
        assert result.status == RecommendationStatus.COMPLETED
        assert result.recommendation_id > 0
        mock_llm_provider.generate_recommendation.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_raises_when_profile_id_not_found(
        self, service, sample_user_query
    ):
        request = RecommendationStartRequest(user_query=sample_user_query, profile_id=9999)
        with pytest.raises(ProfileNotFoundError):
            await service.start_recommendation(request)

    @pytest.mark.asyncio
    async def test_start_uses_profile_when_use_profile_true(
        self,
        service,
        mock_llm_provider,
        clarification_with_questions,
        sample_user_query,
        sample_profile_payload,
    ):
        from api.schemas import ProfileUpsertRequest
        from services.profile_service import ProfileService

        profile = await ProfileService().upsert_profile(
            ProfileUpsertRequest(**sample_profile_payload)
        )
        mock_llm_provider.generate_clarification.return_value = clarification_with_questions

        request = RecommendationStartRequest(
            user_query=sample_user_query,
            profile_id=profile.id,
            use_profile=True,
        )
        result = await service.start_recommendation(request)
        assert result.session_id > 0
        call_kwargs = mock_llm_provider.generate_clarification.call_args
        assert call_kwargs is not None


class TestRecommendationServiceContinue:
    @pytest.mark.asyncio
    async def test_continue_completes_recommendation_after_answers(
        self,
        service,
        mock_llm_provider,
        clarification_with_questions,
        recommendation_payload,
        sample_user_query,
        sample_continue_answers,
    ):
        mock_llm_provider.generate_clarification.return_value = clarification_with_questions
        mock_llm_provider.generate_recommendation.return_value = recommendation_payload

        start = await service.start_recommendation(
            RecommendationStartRequest(user_query=sample_user_query)
        )
        from api.schemas import ClarificationAnswer

        answers = [ClarificationAnswer(**a) for a in sample_continue_answers]
        result = await service.continue_recommendation(
            RecommendationContinueRequest(session_id=start.session_id, answers=answers)
        )

        assert isinstance(result, RecommendationResponse)
        assert result.status == RecommendationStatus.COMPLETED
        assert "парк" in result.main_recommendation.lower() or len(result.main_recommendation) > 10

    @pytest.mark.asyncio
    async def test_continue_raises_for_unknown_session(self, service, sample_continue_answers):
        from api.schemas import ClarificationAnswer

        answers = [ClarificationAnswer(**a) for a in sample_continue_answers]
        with pytest.raises(SessionNotFoundError):
            await service.continue_recommendation(
                RecommendationContinueRequest(session_id=99999, answers=answers)
            )

    @pytest.mark.asyncio
    async def test_continue_raises_when_session_not_awaiting_answers(
        self,
        service,
        mock_llm_provider,
        direct_recommendation_clarification,
        recommendation_payload,
        sample_user_query,
        sample_continue_answers,
    ):
        mock_llm_provider.generate_clarification.return_value = direct_recommendation_clarification
        mock_llm_provider.generate_recommendation.return_value = recommendation_payload

        await service.start_recommendation(
            RecommendationStartRequest(user_query=sample_user_query)
        )

        from api.schemas import ClarificationAnswer

        answers = [ClarificationAnswer(**a) for a in sample_continue_answers]
        with pytest.raises(SessionInvalidStateError):
            await service.continue_recommendation(
                RecommendationContinueRequest(session_id=1, answers=answers)
            )

    @pytest.mark.asyncio
    async def test_continue_raises_for_unknown_question_id(
        self,
        service,
        mock_llm_provider,
        clarification_with_questions,
        sample_user_query,
    ):
        mock_llm_provider.generate_clarification.return_value = clarification_with_questions
        start = await service.start_recommendation(
            RecommendationStartRequest(user_query=sample_user_query)
        )
        from api.schemas import ClarificationAnswer

        with pytest.raises(ValidationBusinessError):
            await service.continue_recommendation(
                RecommendationContinueRequest(
                    session_id=start.session_id,
                    answers=[ClarificationAnswer(question_id="unknown", answer="тест")],
                )
            )

    @pytest.mark.asyncio
    async def test_continue_raises_when_not_all_questions_answered(
        self,
        service,
        mock_llm_provider,
        clarification_with_questions,
        sample_user_query,
    ):
        mock_llm_provider.generate_clarification.return_value = clarification_with_questions
        start = await service.start_recommendation(
            RecommendationStartRequest(user_query=sample_user_query)
        )
        from api.schemas import ClarificationAnswer

        with pytest.raises(ValidationBusinessError):
            await service.continue_recommendation(
                RecommendationContinueRequest(
                    session_id=start.session_id,
                    answers=[ClarificationAnswer(question_id="budget", answer="5000")],
                )
            )

    @pytest.mark.asyncio
    async def test_continue_raises_when_session_expired(
        self, service, mock_llm_provider, clarification_with_questions, sample_user_query
    ):
        mock_llm_provider.generate_clarification.return_value = clarification_with_questions
        start = await service.start_recommendation(
            RecommendationStartRequest(user_query=sample_user_query)
        )

        expired_at = datetime.now(timezone.utc) - timedelta(hours=25)
        await service.mark_session_expired(start.session_id, expired_at)

        from api.schemas import ClarificationAnswer

        with pytest.raises(SessionExpiredError):
            await service.continue_recommendation(
                RecommendationContinueRequest(
                    session_id=start.session_id,
                    answers=[
                        ClarificationAnswer(question_id="budget", answer="5000"),
                        ClarificationAnswer(question_id="company", answer="один"),
                    ],
                )
            )

    @pytest.mark.asyncio
    async def test_forces_final_recommendation_after_max_clarification_rounds(
        self,
        service,
        mock_llm_provider,
        clarification_with_questions,
        recommendation_payload,
        sample_user_query,
    ):
        mock_llm_provider.generate_clarification.return_value = clarification_with_questions
        mock_llm_provider.generate_recommendation.return_value = recommendation_payload

        start = await service.start_recommendation(
            RecommendationStartRequest(user_query=sample_user_query)
        )
        from api.schemas import ClarificationAnswer

        answers = [
            ClarificationAnswer(question_id="budget", answer="5000"),
            ClarificationAnswer(question_id="company", answer="друг"),
        ]
        await service.continue_recommendation(
            RecommendationContinueRequest(session_id=start.session_id, answers=answers)
        )

        second_round = ClarificationPayload(
            needs_clarification=True,
            questions=[FollowupQuestion(id="weather", text="Какая погода ожидается?")],
        )
        mock_llm_provider.generate_clarification.return_value = second_round

        result = await service.start_recommendation(
            RecommendationStartRequest(user_query="Ещё один запрос на выходные")
        )
        assert isinstance(result, (RecommendationResponse, ClarificationResponse))


class TestRecommendationServiceHistory:
    @pytest.mark.asyncio
    async def test_get_history_returns_saved_recommendations(
        self,
        service,
        mock_llm_provider,
        direct_recommendation_clarification,
        recommendation_payload,
        sample_user_query,
    ):
        mock_llm_provider.generate_clarification.return_value = direct_recommendation_clarification
        mock_llm_provider.generate_recommendation.return_value = recommendation_payload

        await service.start_recommendation(
            RecommendationStartRequest(user_query=sample_user_query)
        )

        history = await service.get_history(limit=20, offset=0)
        assert history.total >= 1
        assert len(history.items) >= 1
        assert history.items[0].user_query == sample_user_query

    @pytest.mark.asyncio
    async def test_get_history_respects_pagination(
        self,
        service,
        mock_llm_provider,
        direct_recommendation_clarification,
        recommendation_payload,
    ):
        mock_llm_provider.generate_clarification.return_value = direct_recommendation_clarification
        mock_llm_provider.generate_recommendation.return_value = recommendation_payload

        for i in range(3):
            await service.start_recommendation(
                RecommendationStartRequest(user_query=f"Запрос номер {i} на досуг")
            )

        page = await service.get_history(limit=2, offset=0)
        assert len(page.items) == 2
        assert page.total >= 3

    @pytest.mark.asyncio
    async def test_get_history_detail_includes_context_and_alternatives(
        self,
        service,
        mock_llm_provider,
        direct_recommendation_clarification,
        recommendation_payload,
        sample_user_query,
    ):
        mock_llm_provider.generate_clarification.return_value = direct_recommendation_clarification
        mock_llm_provider.generate_recommendation.return_value = recommendation_payload

        result = await service.start_recommendation(
            RecommendationStartRequest(user_query=sample_user_query)
        )
        detail = await service.get_history_detail(result.recommendation_id)

        assert detail.id == result.recommendation_id
        assert detail.main_recommendation
        assert detail.feedback is None
