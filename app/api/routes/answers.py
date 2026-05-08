from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.auth_deps import (
    AuthenticatedUser,
    get_current_user,
    get_current_user_id,
    resolve_authenticated_user_id,
)
from app.api.deps import get_answer_service
from app.core.errors import AppError
from app.schemas.answer import CreateManualAnswerRequest, DeleteAnswerResponse
from app.schemas.question import QuestionDetailResponse
from app.services.answer_service import AnswerService


router = APIRouter(tags=["answers"])


@router.post(
    "/questions/{question_id}/answers",
    response_model=QuestionDetailResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_manual_answer(
    question_id: int,
    payload: CreateManualAnswerRequest,
    current_user_id: int = Depends(get_current_user_id),
    service: AnswerService = Depends(get_answer_service),
) -> QuestionDetailResponse:
    try:
        normalized_payload = payload.model_copy(
            update={
                "user_id": resolve_authenticated_user_id(
                    current_user_id=current_user_id,
                    requested_user_id=payload.user_id,
                )
            }
        )
        return service.create_manual_answer(question_id=question_id, payload=normalized_payload)
    except AppError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.delete(
    "/answers/{answer_id}",
    response_model=DeleteAnswerResponse,
    status_code=status.HTTP_200_OK,
)
def delete_answer(
    answer_id: int,
    reason: str | None = Query(default=None, max_length=200),
    current_user: AuthenticatedUser = Depends(get_current_user),
    service: AnswerService = Depends(get_answer_service),
) -> DeleteAnswerResponse:
    try:
        return service.delete_answer(
            answer_id=answer_id,
            current_user_id=current_user.user_id,
            current_user_role=current_user.role,
            reason=reason,
        )
    except AppError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
