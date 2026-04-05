from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_feedback_service
from app.core.errors import AppError
from app.schemas.feedback import AnswerFeedbackResponse, SaveAnswerFeedbackRequest
from app.services.feedback_service import FeedbackService


router = APIRouter(prefix="/answers", tags=["feedback"])


@router.post(
    "/{answer_id}/feedback",
    response_model=AnswerFeedbackResponse,
    status_code=status.HTTP_200_OK,
)
def save_feedback(
    answer_id: int,
    payload: SaveAnswerFeedbackRequest,
    service: FeedbackService = Depends(get_feedback_service),
) -> AnswerFeedbackResponse:
    try:
        return service.save_feedback(answer_id=answer_id, payload=payload)
    except AppError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
