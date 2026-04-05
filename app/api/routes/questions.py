from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import get_question_service
from app.core.errors import AppError
from app.schemas.question import (
    AskQuestionRequest,
    QuestionDetailResponse,
    QuestionListResponse,
)
from app.services.question_service import QuestionService


router = APIRouter(prefix="/questions", tags=["questions"])


@router.post(
    "/ask",
    response_model=QuestionDetailResponse,
    status_code=status.HTTP_201_CREATED,
)
def ask_question(
    payload: AskQuestionRequest,
    service: QuestionService = Depends(get_question_service),
) -> QuestionDetailResponse:
    try:
        return service.ask_question(payload)
    except AppError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.get(
    "",
    response_model=QuestionListResponse,
    status_code=status.HTTP_200_OK,
)
def list_questions(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=50),
    category_id: int | None = Query(default=None, gt=0),
    tag_id: int | None = Query(default=None, gt=0),
    status_filter: str | None = Query(default="OPEN", alias="status"),
    service: QuestionService = Depends(get_question_service),
) -> QuestionListResponse:
    try:
        return service.list_questions(
            page=page,
            page_size=page_size,
            category_id=category_id,
            tag_id=tag_id,
            status=status_filter,
        )
    except AppError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.get(
    "/{question_id}",
    response_model=QuestionDetailResponse,
    status_code=status.HTTP_200_OK,
)
def get_question_detail(
    question_id: int,
    service: QuestionService = Depends(get_question_service),
) -> QuestionDetailResponse:
    try:
        return service.get_question_detail(question_id)
    except AppError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
