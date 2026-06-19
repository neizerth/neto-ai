from sqlalchemy.orm import Session

from api.schemas import FeedbackCreateRequest, FeedbackResponse
from config.database import get_db_session
from db.models import Feedback, Recommendation, utc_now
from services.exceptions import FeedbackAlreadyExistsError, RecommendationNotFoundError


class FeedbackService:
    def __init__(self, db: Session | None = None):
        self._db = db
        self._owns_session = db is None

    def _session(self) -> Session:
        if self._db is None:
            self._db = get_db_session()
        return self._db

    async def create_feedback(self, request: FeedbackCreateRequest) -> FeedbackResponse:
        db = self._session()
        recommendation = db.get(Recommendation, request.recommendation_id)
        if recommendation is None:
            raise RecommendationNotFoundError("Рекомендация не найдена")

        existing = (
            db.query(Feedback)
            .filter(Feedback.recommendation_id == request.recommendation_id)
            .first()
        )
        if existing is not None:
            raise FeedbackAlreadyExistsError("Отзыв уже оставлен")

        feedback = Feedback(
            recommendation_id=request.recommendation_id,
            rating=request.rating,
            comment=request.comment,
            created_at=utc_now(),
        )
        db.add(feedback)
        db.commit()
        db.refresh(feedback)

        return FeedbackResponse(
            id=feedback.id,
            recommendation_id=feedback.recommendation_id,
            rating=feedback.rating,
            comment=feedback.comment,
            created_at=feedback.created_at,
        )


def get_feedback_service() -> FeedbackService:
    return FeedbackService()
