from fastapi import APIRouter, Depends, status

from api.schemas import FeedbackCreateRequest, FeedbackResponse
from services.exceptions import AppError
from services.feedback_service import FeedbackService, get_feedback_service

router = APIRouter(tags=["feedback"])


@router.post("/feedback", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
async def create_feedback(
    request: FeedbackCreateRequest,
    service: FeedbackService = Depends(get_feedback_service),
) -> FeedbackResponse:
    try:
        return await service.create_feedback(request)
    except AppError:
        raise
