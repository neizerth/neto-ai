from datetime import datetime
from enum import Enum
from typing import Annotated, Literal, Union

from pydantic import BaseModel, Field, field_validator, model_validator

from llm.schemas import AlternativeOption, FollowupQuestion


class ActivityLevel(str, Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"


class BudgetRange(str, Enum):
    FREE = "free"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    FLEXIBLE = "flexible"


class SessionStatus(str, Enum):
    COLLECTING_CONTEXT = "collecting_context"
    AWAITING_ANSWERS = "awaiting_answers"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"


class RecommendationStatus(str, Enum):
    NEEDS_CLARIFICATION = "needs_clarification"
    COMPLETED = "completed"


class RecommendationStartRequest(BaseModel):
    user_query: str = Field(..., min_length=5, max_length=1000)
    profile_id: int | None = Field(default=None, ge=1)
    use_profile: bool = True

    @field_validator("user_query")
    @classmethod
    def normalize_query(cls, v: str) -> str:
        v = " ".join(v.split())
        if len(v) < 5:
            raise ValueError("Запрос слишком короткий — опишите ситуацию подробнее")
        return v


class ClarificationAnswer(BaseModel):
    question_id: str = Field(..., min_length=1, max_length=50)
    answer: str = Field(..., min_length=1, max_length=500)

    @field_validator("answer", "question_id")
    @classmethod
    def strip_value(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Поле не может быть пустым")
        return v


class RecommendationContinueRequest(BaseModel):
    session_id: int = Field(..., ge=1)
    answers: list[ClarificationAnswer] = Field(..., min_length=1, max_length=10)


class ProfileUpsertRequest(BaseModel):
    budget: BudgetRange | None = None
    activity_level: ActivityLevel | None = None
    favorite_activities: list[str] = Field(default_factory=list, max_length=20)
    disliked_activities: list[str] = Field(default_factory=list, max_length=20)

    @field_validator("favorite_activities", "disliked_activities")
    @classmethod
    def normalize_activities(cls, v: list[str]) -> list[str]:
        normalized: list[str] = []
        for item in v:
            item = item.strip()
            if item and item not in normalized:
                normalized.append(item)
        return normalized[:20]

    @model_validator(mode="after")
    def resolve_favorite_disliked_overlap(self) -> "ProfileUpsertRequest":
        disliked = set(self.disliked_activities)
        self.favorite_activities = [a for a in self.favorite_activities if a not in disliked]
        return self


class FeedbackCreateRequest(BaseModel):
    recommendation_id: int = Field(..., ge=1)
    rating: int = Field(..., ge=1, le=5)
    comment: str | None = Field(default=None, max_length=1000)

    @field_validator("comment")
    @classmethod
    def normalize_comment(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = v.strip()
        return v or None


class ClarificationResponse(BaseModel):
    status: Literal[RecommendationStatus.NEEDS_CLARIFICATION] = (
        RecommendationStatus.NEEDS_CLARIFICATION
    )
    session_id: int
    questions: list[FollowupQuestion]
    message: str | None = None


class RecommendationResponse(BaseModel):
    status: Literal[RecommendationStatus.COMPLETED] = RecommendationStatus.COMPLETED
    recommendation_id: int
    session_id: int
    user_query: str
    main_recommendation: str
    alternatives: list[AlternativeOption]
    reasoning: str
    budget_estimation: str
    time_estimation: str
    created_at: datetime


RecommendationStartResponse = Annotated[
    Union[ClarificationResponse, RecommendationResponse],
    Field(discriminator="status"),
]


class ProfileResponse(BaseModel):
    id: int
    budget: BudgetRange | None
    activity_level: ActivityLevel | None
    favorite_activities: list[str]
    disliked_activities: list[str]
    created_at: datetime
    updated_at: datetime


class HistoryItem(BaseModel):
    id: int
    user_query: str
    main_recommendation: str
    budget_estimation: str
    time_estimation: str
    created_at: datetime
    has_feedback: bool


class HistoryResponse(BaseModel):
    items: list[HistoryItem]
    total: int
    limit: int
    offset: int


class FeedbackDetail(BaseModel):
    id: int
    rating: int
    comment: str | None
    created_at: datetime


class HistoryDetailResponse(BaseModel):
    id: int
    session_id: int
    user_query: str
    context: dict[str, str]
    main_recommendation: str
    alternatives: list[AlternativeOption]
    reasoning: str
    budget_estimation: str
    time_estimation: str
    created_at: datetime
    feedback: FeedbackDetail | None


class FeedbackResponse(BaseModel):
    id: int
    recommendation_id: int
    rating: int
    comment: str | None
    created_at: datetime


class ErrorResponse(BaseModel):
    detail: str
    error_code: str | None = None


def to_recommendation_response(
    payload,
    *,
    recommendation_id: int,
    session_id: int,
    user_query: str,
    created_at: datetime,
) -> RecommendationResponse:
    return RecommendationResponse(
        recommendation_id=recommendation_id,
        session_id=session_id,
        user_query=user_query,
        main_recommendation=payload.main_recommendation,
        alternatives=payload.alternatives,
        reasoning=payload.reasoning,
        budget_estimation=payload.budget_estimation,
        time_estimation=payload.time_estimation,
        created_at=created_at,
    )
