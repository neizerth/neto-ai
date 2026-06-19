import re
from enum import Enum

from pydantic import BaseModel, Field, field_validator, model_validator


class UsageProfile(str, Enum):
    EVERYDAY = "everyday"
    GAMING = "gaming"
    PHOTOGRAPHY = "photography"
    PRO_PHOTOGRAPHY = "pro_photography"
    VIDEO_CREATION = "video_creation"
    BUSINESS = "business"
    BATTERY_LIFE = "battery_life"
    COMPACT = "compact"


class UpgradeUrgency(str, Enum):
    NOT_NEEDED = "not_needed"
    OPTIONAL = "optional"
    RECOMMENDED = "recommended"
    URGENT = "urgent"


class RecommendRequest(BaseModel):
    current_phone: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Текущая модель телефона",
        examples=["iPhone 12", "Samsung Galaxy S21 Ultra"],
    )
    usage_profile: UsageProfile = Field(
        ...,
        description="Основной сценарий использования",
    )
    additional_requirements: str | None = Field(
        default=None,
        max_length=500,
        description="Дополнительные пожелания",
    )
    max_recommendations: int = Field(
        default=3,
        ge=1,
        le=5,
        description="Максимальное число рекомендуемых моделей",
    )

    @field_validator("current_phone")
    @classmethod
    def normalize_phone_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Название модели не может быть пустым")
        return re.sub(r"\s+", " ", v)

    @field_validator("additional_requirements")
    @classmethod
    def strip_requirements(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = v.strip()
        return v or None


class LLMPhoneRecommendation(BaseModel):
    brand: str = Field(..., min_length=1, max_length=50)
    model: str = Field(..., min_length=1, max_length=100)
    full_name: str = Field(..., min_length=2, max_length=150)
    reason: str = Field(..., min_length=10, max_length=500)
    estimated_price_range: str | None = Field(default=None, max_length=100)


class LLMRecommendationPayload(BaseModel):
    upgrade_needed: bool
    urgency: UpgradeUrgency
    summary: str = Field(..., min_length=10, max_length=1000)
    current_phone_assessment: str = Field(..., min_length=10, max_length=500)
    recommendations: list[LLMPhoneRecommendation] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_recommendations_consistency(self) -> "LLMRecommendationPayload":
        if not self.upgrade_needed and self.recommendations:
            raise ValueError(
                "Если upgrade_needed=false, список recommendations должен быть пустым"
            )
        if self.upgrade_needed and self.urgency == UpgradeUrgency.NOT_NEEDED:
            raise ValueError("upgrade_needed=true несовместимо с urgency=not_needed")
        if not self.upgrade_needed and self.urgency != UpgradeUrgency.NOT_NEEDED:
            raise ValueError("При upgrade_needed=false urgency должен быть not_needed")
        return self


class PhoneRecommendation(BaseModel):
    brand: str
    model: str
    full_name: str
    reason: str
    estimated_price_range: str | None = None


class RecommendResponse(BaseModel):
    upgrade_needed: bool
    urgency: UpgradeUrgency
    summary: str
    current_phone_assessment: str
    recommendations: list[PhoneRecommendation]
    usage_profile: UsageProfile
    current_phone: str


class ErrorResponse(BaseModel):
    detail: str
    error_code: str | None = None


def to_api_response(
    payload: LLMRecommendationPayload,
    request: RecommendRequest,
) -> RecommendResponse:
    return RecommendResponse(
        upgrade_needed=payload.upgrade_needed,
        urgency=payload.urgency,
        summary=payload.summary,
        current_phone_assessment=payload.current_phone_assessment,
        recommendations=[
            PhoneRecommendation(**rec.model_dump())
            for rec in payload.recommendations
        ],
        usage_profile=request.usage_profile,
        current_phone=request.current_phone,
    )
