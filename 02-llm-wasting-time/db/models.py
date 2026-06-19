import json
from datetime import datetime, timezone

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class UserProfile(Base):
    __tablename__ = "user_profile"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    budget: Mapped[str | None] = mapped_column(Text, nullable=True)
    activity_level: Mapped[str | None] = mapped_column(Text, nullable=True)
    favorite_activities: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    disliked_activities: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    def get_favorite_activities(self) -> list[str]:
        return json.loads(self.favorite_activities)

    def get_disliked_activities(self) -> list[str]:
        return json.loads(self.disliked_activities)

    def to_dict(self) -> dict:
        return {
            "budget": self.budget,
            "activity_level": self.activity_level,
            "favorite_activities": self.get_favorite_activities(),
            "disliked_activities": self.get_disliked_activities(),
        }


class RecommendationSession(Base):
    __tablename__ = "recommendation_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    profile_id: Mapped[int | None] = mapped_column(ForeignKey("user_profile.id"), nullable=True)
    user_query: Mapped[str] = mapped_column(Text, nullable=False)
    context: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    status: Mapped[str] = mapped_column(Text, nullable=False)
    pending_questions: Mapped[str | None] = mapped_column(Text, nullable=True)
    clarification_rounds: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    recommendation: Mapped["Recommendation | None"] = relationship(back_populates="session")

    def get_context(self) -> dict[str, str]:
        return json.loads(self.context)

    def set_context(self, value: dict[str, str]) -> None:
        self.context = json.dumps(value, ensure_ascii=False)


class Recommendation(Base):
    __tablename__ = "recommendations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("recommendation_sessions.id"), nullable=False, unique=True
    )
    user_query: Mapped[str] = mapped_column(Text, nullable=False)
    context: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    recommendation: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    session: Mapped[RecommendationSession] = relationship(back_populates="recommendation")
    feedback: Mapped["Feedback | None"] = relationship(back_populates="recommendation")

    def get_context(self) -> dict[str, str]:
        return json.loads(self.context)

    def get_payload(self) -> dict:
        return json.loads(self.recommendation)


class Feedback(Base):
    __tablename__ = "feedback"
    __table_args__ = (
        UniqueConstraint("recommendation_id"),
        CheckConstraint("rating BETWEEN 1 AND 5", name="rating_range"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    recommendation_id: Mapped[int] = mapped_column(
        ForeignKey("recommendations.id"), nullable=False, unique=True
    )
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    recommendation: Mapped[Recommendation] = relationship(back_populates="feedback")
