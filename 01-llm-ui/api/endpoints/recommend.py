from fastapi import APIRouter, Depends, HTTPException

from api.schemas import ErrorResponse, RecommendRequest, RecommendResponse
from services.exceptions import LLMError, LLMParseError
from services.recommendation import RecommendationService, get_recommendation_service

router = APIRouter(tags=["recommendations"])


@router.post(
    "/recommend",
    response_model=RecommendResponse,
    responses={
        502: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
    summary="Рекомендация по обновлению смартфона",
)
async def recommend(
    request: RecommendRequest,
    service: RecommendationService = Depends(get_recommendation_service),
) -> RecommendResponse:
    try:
        return await service.recommend(request)
    except LLMParseError as e:
        raise HTTPException(
            status_code=502,
            detail={"detail": str(e), "error_code": "LLM_PARSE_ERROR"},
        ) from e
    except LLMError as e:
        raise HTTPException(
            status_code=502,
            detail={"detail": str(e), "error_code": "LLM_ERROR"},
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"detail": "Внутренняя ошибка сервера", "error_code": "INTERNAL_ERROR"},
        ) from e
