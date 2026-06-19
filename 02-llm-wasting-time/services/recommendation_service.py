import json
from datetime import datetime, timedelta, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from api.schemas import (
    ClarificationResponse,
    FeedbackDetail,
    HistoryDetailResponse,
    HistoryItem,
    HistoryResponse,
    RecommendationContinueRequest,
    RecommendationStartRequest,
    SessionStatus,
    to_recommendation_response,
)
from config.database import get_db_session
from config.settings import Settings, get_settings
from db.models import Feedback, Recommendation, RecommendationSession, utc_now
from llm.base_provider import BaseLLMProvider, _to_clarification, _to_recommendation
from llm.fake_provider import FakeLLMProvider
from llm.openai_provider import OpenAIProvider
from llm.schemas import ClarificationPayload, FollowupQuestion, RecommendationPayload
from services.exceptions import (
    ProfileNotFoundError,
    RecommendationNotFoundError,
    SessionExpiredError,
    SessionInvalidStateError,
    SessionNotFoundError,
    ValidationBusinessError,
)
from services.profile_service import ProfileService


class RecommendationService:
    def __init__(
        self,
        llm_provider: BaseLLMProvider | None = None,
        db: Session | None = None,
        settings: Settings | None = None,
    ):
        self._settings = settings or get_settings()
        self._llm = llm_provider or _create_llm_provider(self._settings)
        self._db = db
        self._owns_session = db is None

    def _session(self) -> Session:
        if self._db is None:
            self._db = get_db_session()
        return self._db

    def _check_session_expired(self, session: RecommendationSession) -> None:
        ttl = timedelta(hours=self._settings.session_ttl_hours)
        reference = session.updated_at or session.created_at
        if reference.tzinfo is None:
            reference = reference.replace(tzinfo=timezone.utc)
        if datetime.now(timezone.utc) - reference > ttl:
            session.status = SessionStatus.EXPIRED.value
            self._session().commit()
            raise SessionExpiredError("Сессия истекла")

    async def _resolve_profile(
        self, request: RecommendationStartRequest
    ) -> tuple[int | None, dict | None]:
        if request.profile_id is not None:
            profile_svc = ProfileService(db=self._session())
            profile = await profile_svc.get_profile_by_id(request.profile_id)
            return profile.id, profile.to_dict() if request.use_profile else None

        if request.use_profile:
            profile_svc = ProfileService(db=self._session())
            try:
                profile_resp = await profile_svc.get_profile()
                profile = await profile_svc.get_profile_by_id(profile_resp.id)
                return profile.id, profile.to_dict()
            except ProfileNotFoundError:
                return None, None

        return None, None

    async def _save_recommendation(
        self,
        session: RecommendationSession,
        payload: RecommendationPayload,
    ):
        db = self._session()
        session.status = SessionStatus.COMPLETED.value
        session.pending_questions = None
        session.updated_at = utc_now()
        db.add(session)
        db.flush()

        rec = Recommendation(
            session_id=session.id,
            user_query=session.user_query,
            context=session.context,
            recommendation=payload.model_dump_json(),
            created_at=utc_now(),
        )
        db.add(rec)
        db.commit()
        db.refresh(rec)
        db.refresh(session)
        return rec

    async def start_recommendation(self, request: RecommendationStartRequest):
        db = self._session()
        profile_id, profile_dict = await self._resolve_profile(request)

        session = RecommendationSession(
            profile_id=profile_id,
            user_query=request.user_query,
            context="{}",
            status=SessionStatus.COLLECTING_CONTEXT.value,
            clarification_rounds=0,
            created_at=utc_now(),
            updated_at=utc_now(),
        )
        db.add(session)
        db.commit()
        db.refresh(session)

        clarification_raw = await self._llm.generate_clarification(
            request.user_query, profile_dict
        )
        clarification = _to_clarification(clarification_raw)

        context = session.get_context()
        context.update(clarification.extracted_context)

        if clarification.needs_clarification:
            session.status = SessionStatus.AWAITING_ANSWERS.value
            session.pending_questions = json.dumps(
                [q.model_dump() for q in clarification.questions], ensure_ascii=False
            )
            session.set_context(context)
            session.clarification_rounds += 1
            session.updated_at = utc_now()
            db.commit()

            return ClarificationResponse(
                session_id=session.id,
                questions=clarification.questions,
                message="Чтобы предложить подходящие варианты, уточните несколько деталей.",
            )

        session.set_context(context)
        recommendation = await self._llm.generate_recommendation(
            request.user_query, context, profile_dict
        )
        payload = _to_recommendation(recommendation)
        rec = await self._save_recommendation(session, payload)
        return to_recommendation_response(
            payload,
            recommendation_id=rec.id,
            session_id=session.id,
            user_query=session.user_query,
            created_at=rec.created_at,
        )

    async def continue_recommendation(self, request: RecommendationContinueRequest):
        db = self._session()
        session = db.get(RecommendationSession, request.session_id)
        if session is None:
            raise SessionNotFoundError("Сессия не найдена")

        self._check_session_expired(session)

        if session.status != SessionStatus.AWAITING_ANSWERS.value:
            raise SessionInvalidStateError("Сессия не ожидает ответов")

        if not session.pending_questions:
            raise SessionInvalidStateError("Сессия не ожидает ответов")

        pending = [
            FollowupQuestion.model_validate(q)
            for q in json.loads(session.pending_questions)
        ]
        pending_ids = {q.id for q in pending}
        answer_ids = {a.question_id for a in request.answers}

        if not answer_ids.issubset(pending_ids):
            raise ValidationBusinessError("Неизвестный вопрос")

        if answer_ids != pending_ids:
            raise ValidationBusinessError("Ответьте на все вопросы")

        context = session.get_context()
        for answer in request.answers:
            context[answer.question_id] = answer.answer
        session.set_context(context)
        session.pending_questions = None
        session.updated_at = utc_now()
        db.commit()

        profile_dict = None
        if session.profile_id:
            profile_svc = ProfileService(db=db)
            try:
                profile = await profile_svc.get_profile_by_id(session.profile_id)
                profile_dict = profile.to_dict()
            except ProfileNotFoundError:
                pass

        recommendation = await self._llm.generate_recommendation(
            session.user_query, context, profile_dict
        )
        payload = _to_recommendation(recommendation)
        rec = await self._save_recommendation(session, payload)
        return to_recommendation_response(
            payload,
            recommendation_id=rec.id,
            session_id=session.id,
            user_query=session.user_query,
            created_at=rec.created_at,
        )

    async def mark_session_expired(self, session_id: int, expired_at: datetime) -> None:
        db = self._session()
        session = db.get(RecommendationSession, session_id)
        if session is None:
            raise SessionNotFoundError("Сессия не найдена")
        session.updated_at = expired_at
        db.commit()

    async def get_history(self, limit: int, offset: int) -> HistoryResponse:
        db = self._session()
        total = db.query(func.count(Recommendation.id)).scalar() or 0
        rows = (
            db.query(Recommendation)
            .order_by(Recommendation.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

        items = []
        for rec in rows:
            payload = RecommendationPayload.model_validate(rec.get_payload())
            has_feedback = rec.feedback is not None
            items.append(
                HistoryItem(
                    id=rec.id,
                    user_query=rec.user_query,
                    main_recommendation=payload.main_recommendation,
                    budget_estimation=payload.budget_estimation,
                    time_estimation=payload.time_estimation,
                    created_at=rec.created_at,
                    has_feedback=has_feedback,
                )
            )

        return HistoryResponse(items=items, total=total, limit=limit, offset=offset)

    async def get_history_detail(self, recommendation_id: int) -> HistoryDetailResponse:
        db = self._session()
        rec = db.get(Recommendation, recommendation_id)
        if rec is None:
            raise RecommendationNotFoundError("Рекомендация не найдена")

        payload = RecommendationPayload.model_validate(rec.get_payload())
        feedback_detail = None
        if rec.feedback:
            feedback_detail = FeedbackDetail(
                id=rec.feedback.id,
                rating=rec.feedback.rating,
                comment=rec.feedback.comment,
                created_at=rec.feedback.created_at,
            )

        return HistoryDetailResponse(
            id=rec.id,
            session_id=rec.session_id,
            user_query=rec.user_query,
            context=rec.get_context(),
            main_recommendation=payload.main_recommendation,
            alternatives=payload.alternatives,
            reasoning=payload.reasoning,
            budget_estimation=payload.budget_estimation,
            time_estimation=payload.time_estimation,
            created_at=rec.created_at,
            feedback=feedback_detail,
        )


def _create_llm_provider(settings: Settings) -> BaseLLMProvider:
    if settings.openai_api_key == "test-key":
        return FakeLLMProvider()
    return OpenAIProvider(settings)


def get_recommendation_service() -> RecommendationService:
    return RecommendationService()
