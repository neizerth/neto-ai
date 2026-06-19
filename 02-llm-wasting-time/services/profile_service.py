import json
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from api.schemas import (
    ActivityLevel,
    BudgetRange,
    ProfileResponse,
    ProfileUpsertRequest,
)
from config.database import get_db_session
from db.models import UserProfile, utc_now
from services.exceptions import ProfileNotFoundError


class ProfileService:
    def __init__(self, db: Session | None = None):
        self._db = db
        self._owns_session = db is None

    def _session(self) -> Session:
        if self._db is None:
            self._db = get_db_session()
        return self._db

    def _to_response(self, profile: UserProfile) -> ProfileResponse:
        return ProfileResponse(
            id=profile.id,
            budget=BudgetRange(profile.budget) if profile.budget else None,
            activity_level=ActivityLevel(profile.activity_level) if profile.activity_level else None,
            favorite_activities=profile.get_favorite_activities(),
            disliked_activities=profile.get_disliked_activities(),
            created_at=profile.created_at,
            updated_at=profile.updated_at,
        )

    async def get_profile(self) -> ProfileResponse:
        db = self._session()
        profile = db.query(UserProfile).order_by(UserProfile.id).first()
        if profile is None:
            raise ProfileNotFoundError("Профиль не найден")
        return self._to_response(profile)

    async def get_profile_by_id(self, profile_id: int) -> UserProfile:
        db = self._session()
        profile = db.get(UserProfile, profile_id)
        if profile is None:
            raise ProfileNotFoundError("Профиль не найден")
        return profile

    async def upsert_profile(self, request: ProfileUpsertRequest) -> ProfileResponse:
        db = self._session()
        profile = db.query(UserProfile).order_by(UserProfile.id).first()
        now = utc_now()

        if profile is None:
            profile = UserProfile(
                budget=request.budget.value if request.budget else None,
                activity_level=request.activity_level.value if request.activity_level else None,
                favorite_activities=json.dumps(request.favorite_activities, ensure_ascii=False),
                disliked_activities=json.dumps(request.disliked_activities, ensure_ascii=False),
                created_at=now,
                updated_at=now,
            )
            db.add(profile)
        else:
            profile.budget = request.budget.value if request.budget else None
            profile.activity_level = (
                request.activity_level.value if request.activity_level else None
            )
            profile.favorite_activities = json.dumps(request.favorite_activities, ensure_ascii=False)
            profile.disliked_activities = json.dumps(request.disliked_activities, ensure_ascii=False)
            profile.updated_at = now

        db.commit()
        db.refresh(profile)
        return self._to_response(profile)


def get_profile_service() -> ProfileService:
    return ProfileService()
