from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_answer_service
from app.core.errors import AppError
from app.schemas.answer import CreateManualAnswerRequest
from app.schemas.question import QuestionDetailResponse
from app.services.answer_service import AnswerService


router = APIRouter(prefix="/questions", tags=["answers"])


@router.post(
    "/{question_id}/answers",
    response_model=QuestionDetailResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_manual_answer(
    question_id: int,
    payload: CreateManualAnswerRequest,
    service: AnswerService = Depends(get_answer_service),
) -> QuestionDetailResponse:
    try:
        return service.create_manual_answer(question_id=question_id, payload=payload)
    except AppError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

