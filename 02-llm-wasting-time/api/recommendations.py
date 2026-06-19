from fastapi import APIRouter, Depends, Query

from api.schemas import (
    ClarificationResponse,
    HistoryDetailResponse,
    HistoryResponse,
    RecommendationContinueRequest,
    RecommendationResponse,
    RecommendationStartRequest,
    RecommendationStartResponse,
)
from services.exceptions import AppError
from services.recommendation_service import RecommendationService, get_recommendation_service

router = APIRouter(prefix="/recommendation", tags=["recommendations"])
history_router = APIRouter(tags=["history"])


@router.post("", response_model=RecommendationStartResponse)
async def start_recommendation(
    request: RecommendationStartRequest,
    service: RecommendationService = Depends(get_recommendation_service),
) -> ClarificationResponse | RecommendationResponse:
    try:
        return await service.start_recommendation(request)
    except AppError:
        raise


@router.post("/continue", response_model=RecommendationResponse)
async def continue_recommendation(
    request: RecommendationContinueRequest,
    service: RecommendationService = Depends(get_recommendation_service),
) -> RecommendationResponse:
    try:
        return await service.continue_recommendation(request)
    except AppError:
        raise


@history_router.get("/history", response_model=HistoryResponse)
async def list_history(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    service: RecommendationService = Depends(get_recommendation_service),
) -> HistoryResponse:
    return await service.get_history(limit=limit, offset=offset)


@history_router.get("/history/{recommendation_id}", response_model=HistoryDetailResponse)
async def get_history_detail(
    recommendation_id: int,
    service: RecommendationService = Depends(get_recommendation_service),
) -> HistoryDetailResponse:
    try:
        return await service.get_history_detail(recommendation_id)
    except AppError:
        raise
