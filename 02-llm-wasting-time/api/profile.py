from fastapi import APIRouter, Depends

from api.schemas import ProfileResponse, ProfileUpsertRequest
from services.exceptions import AppError
from services.profile_service import ProfileService, get_profile_service

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("", response_model=ProfileResponse)
async def get_profile(
    service: ProfileService = Depends(get_profile_service),
) -> ProfileResponse:
    try:
        return await service.get_profile()
    except AppError:
        raise


@router.put("", response_model=ProfileResponse)
async def upsert_profile(
    request: ProfileUpsertRequest,
    service: ProfileService = Depends(get_profile_service),
) -> ProfileResponse:
    return await service.upsert_profile(request)
