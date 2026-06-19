"""
Unit-тесты Pydantic-схем API.

Спецификация: docs/models.md, docs/validation.md
"""

import pytest
from pydantic import ValidationError

from api.schemas import (
    ActivityLevel,
    BudgetRange,
    ClarificationAnswer,
    FeedbackCreateRequest,
    ProfileUpsertRequest,
    RecommendationContinueRequest,
    RecommendationStartRequest,
    RecommendationStatus,
    SessionStatus,
    to_recommendation_response,
)
from llm.schemas import (
    AlternativeOption,
    ClarificationPayload,
    FollowupQuestion,
    RecommendationPayload,
)


# --- RecommendationStartRequest ---


class TestRecommendationStartRequest:
    def test_valid_request(self, sample_user_query):
        req = RecommendationStartRequest(user_query=sample_user_query)
        assert req.user_query == sample_user_query
        assert req.use_profile is True
        assert req.profile_id is None

    @pytest.mark.parametrize("query", ["", " ", "да", "а" * 4])
    def test_rejects_too_short_query(self, query):
        with pytest.raises(ValidationError):
            RecommendationStartRequest(user_query=query)

    def test_normalizes_whitespace(self):
        req = RecommendationStartRequest(
            user_query="  Не   знаю,  как  провести  субботу  "
        )
        assert req.user_query == "Не знаю, как провести субботу"

    def test_rejects_query_over_1000_chars(self):
        with pytest.raises(ValidationError):
            RecommendationStartRequest(user_query="x" * 1001)

    def test_profile_id_must_be_positive(self):
        with pytest.raises(ValidationError):
            RecommendationStartRequest(user_query="Не знаю, как провести субботу", profile_id=0)


# --- RecommendationContinueRequest ---


class TestRecommendationContinueRequest:
    def test_valid_continue_request(self, sample_continue_answers):
        answers = [ClarificationAnswer(**a) for a in sample_continue_answers]
        req = RecommendationContinueRequest(session_id=1, answers=answers)
        assert req.session_id == 1
        assert len(req.answers) == 2

    def test_rejects_empty_answers(self):
        with pytest.raises(ValidationError):
            RecommendationContinueRequest(session_id=1, answers=[])

    def test_rejects_empty_answer_text(self):
        with pytest.raises(ValidationError):
            ClarificationAnswer(question_id="budget", answer="  ")

    def test_strips_answer_whitespace(self):
        ans = ClarificationAnswer(question_id="budget", answer="  До 5000 ₽  ")
        assert ans.answer == "До 5000 ₽"


# --- ProfileUpsertRequest ---


class TestProfileUpsertRequest:
    def test_valid_profile(self, sample_profile_payload):
        req = ProfileUpsertRequest(**sample_profile_payload)
        assert req.budget == BudgetRange.MEDIUM
        assert req.activity_level == ActivityLevel.MODERATE
        assert "кино" in req.favorite_activities

    def test_deduplicates_activities(self):
        req = ProfileUpsertRequest(
            favorite_activities=["кино", " кино ", "прогулки"],
            disliked_activities=[],
        )
        assert req.favorite_activities == ["кино", "прогулки"]

    def test_disliked_removes_from_favorites(self):
        req = ProfileUpsertRequest(
            favorite_activities=["кино", "клубы"],
            disliked_activities=["клубы"],
        )
        assert "клубы" not in req.favorite_activities
        assert "клубы" in req.disliked_activities

    def test_rejects_more_than_20_activities(self):
        activities = [f"активность_{i}" for i in range(25)]
        with pytest.raises(ValidationError):
            ProfileUpsertRequest(favorite_activities=activities)


# --- FeedbackCreateRequest ---


class TestFeedbackCreateRequest:
    def test_valid_feedback(self, sample_feedback_payload):
        req = FeedbackCreateRequest(**sample_feedback_payload)
        assert req.rating == 5
        assert req.comment == "Отличная идея!"

    @pytest.mark.parametrize("rating", [0, 6, -1])
    def test_rejects_invalid_rating(self, rating):
        with pytest.raises(ValidationError):
            FeedbackCreateRequest(recommendation_id=1, rating=rating)

    def test_empty_comment_becomes_none(self):
        req = FeedbackCreateRequest(recommendation_id=1, rating=4, comment="   ")
        assert req.comment is None


# --- LLM schemas: ClarificationPayload ---


class TestClarificationPayload:
    def test_valid_with_questions(self, sample_clarification_payload):
        payload = ClarificationPayload(**sample_clarification_payload)
        assert payload.needs_clarification is True
        assert len(payload.questions) == 2

    def test_needs_clarification_without_questions_fails(self):
        with pytest.raises(ValidationError):
            ClarificationPayload(needs_clarification=True, questions=[])

    def test_no_clarification_with_questions_fails(self):
        with pytest.raises(ValidationError):
            ClarificationPayload(
                needs_clarification=False,
                questions=[
                    FollowupQuestion(id="q1", text="Какой бюджет на день?")
                ],
            )

    def test_rejects_more_than_5_questions(self):
        questions = [
            FollowupQuestion(id=f"q{i}", text=f"Вопрос номер {i} для уточнения?")
            for i in range(6)
        ]
        with pytest.raises(ValidationError):
            ClarificationPayload(needs_clarification=True, questions=questions)

    def test_rejects_duplicate_question_ids(self):
        with pytest.raises(ValidationError):
            ClarificationPayload(
                needs_clarification=True,
                questions=[
                    FollowupQuestion(id="budget", text="Какой бюджет на день?"),
                    FollowupQuestion(id="budget", text="Сколько готовы потратить?"),
                ],
            )


# --- LLM schemas: RecommendationPayload ---


class TestRecommendationPayload:
    def test_valid_recommendation(self, sample_recommendation_payload):
        payload = RecommendationPayload(**sample_recommendation_payload)
        assert len(payload.main_recommendation) >= 10
        assert len(payload.alternatives) == 1

    def test_rejects_more_than_5_alternatives(self, sample_recommendation_payload):
        data = sample_recommendation_payload.copy()
        data["alternatives"] = [
            {
                "title": f"Вариант {i}",
                "description": "Описание варианта досуга для теста.",
                "budget_estimation": "1000 ₽",
                "time_estimation": "2 часа",
            }
            for i in range(6)
        ]
        with pytest.raises(ValidationError):
            RecommendationPayload(**data)

    def test_rejects_short_main_recommendation(self, sample_recommendation_payload):
        data = sample_recommendation_payload.copy()
        data["main_recommendation"] = "коротко"
        with pytest.raises(ValidationError):
            RecommendationPayload(**data)

    def test_rejects_duplicate_alternative_titles(self, sample_recommendation_payload):
        data = sample_recommendation_payload.copy()
        alt = data["alternatives"][0]
        data["alternatives"] = [alt, alt]
        with pytest.raises(ValidationError):
            RecommendationPayload(**data)


# --- Enums ---


class TestEnums:
    def test_session_status_values(self):
        assert SessionStatus.AWAITING_ANSWERS == "awaiting_answers"
        assert SessionStatus.COMPLETED == "completed"

    def test_recommendation_status_values(self):
        assert RecommendationStatus.NEEDS_CLARIFICATION == "needs_clarification"
        assert RecommendationStatus.COMPLETED == "completed"


# --- Mapper ---


class TestToRecommendationResponse:
    def test_maps_payload_to_api_response(
        self, sample_recommendation_payload, fixed_datetime
    ):
        payload = RecommendationPayload(**sample_recommendation_payload)
        response = to_recommendation_response(
            payload,
            recommendation_id=1,
            session_id=42,
            user_query="Не знаю, как провести субботу",
            created_at=fixed_datetime,
        )
        assert response.recommendation_id == 1
        assert response.session_id == 42
        assert response.status == RecommendationStatus.COMPLETED
        assert response.main_recommendation == payload.main_recommendation
