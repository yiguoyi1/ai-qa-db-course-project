from fastapi import APIRouter, Depends, HTTPException, status

from app.api.auth_deps import get_current_user_id, resolve_authenticated_user_id
from app.api.deps import get_feedback_service
from app.core.errors import AppError
from app.schemas.feedback import AnswerFeedbackResponse, SaveAnswerFeedbackRequest
from app.services.feedback_service import FeedbackService


router = APIRouter(tags=["feedback"])


@router.post(
    "/answers/{answer_id}/feedback",
    response_model=AnswerFeedbackResponse,
    status_code=status.HTTP_200_OK,
)
def save_feedback(
    answer_id: int,
    payload: SaveAnswerFeedbackRequest,
    current_user_id: int = Depends(get_current_user_id),
    service: FeedbackService = Depends(get_feedback_service),
) -> AnswerFeedbackResponse:
    try:
        normalized_payload = payload.model_copy(
            update={
                "user_id": resolve_authenticated_user_id(
                    current_user_id=current_user_id,
                    requested_user_id=payload.user_id,
                )
            }
        )
        return service.save_feedback(answer_id=answer_id, payload=normalized_payload)
    except AppError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.get(
    "/questions/{question_id}/feedbacks",
    response_model=dict[int, str],
    status_code=status.HTTP_200_OK,
)
def list_question_feedbacks(
    question_id: int,
    current_user_id: int = Depends(get_current_user_id),
    service: FeedbackService = Depends(get_feedback_service),
) -> dict[int, str]:
    try:
        return service.list_question_feedbacks(
            question_id=question_id,
            user_id=current_user_id,
        )
    except AppError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
