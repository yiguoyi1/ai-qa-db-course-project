from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.auth_deps import get_current_user_id, resolve_authenticated_user_id
from app.api.deps import get_question_service
from app.core.errors import AppError
from app.schemas.question import (
    AskQuestionRequest,
    FeedbackRequest,
    QuestionCreate,
    QuestionDetailResponse,
    QuestionListItem,
    QuestionListResponse,
)
from app.services.answer_service import AnswerService
from app.services.question_service import QuestionService

router = APIRouter(prefix="/questions", tags=["questions"])


@router.post(
    "/ask",
    response_model=QuestionDetailResponse,
    status_code=status.HTTP_201_CREATED,
)
def ask_question(
    payload: AskQuestionRequest,
    current_user_id: int = Depends(get_current_user_id),
    service: QuestionService = Depends(get_question_service),
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
        return service.ask_question(normalized_payload)
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


@router.get("", response_model=list[QuestionListItem])
def list_questions(question_service: QuestionService = Depends(get_question_service)):
    return question_service.get_questions()

# 🌟 终于！开设接收纯社区发帖的 POST 大门 🌟
@router.post("")
def create_community_question(
    payload: QuestionCreate,
    current_user_id: int = Depends(get_current_user_id),
    service: QuestionService = Depends(get_question_service),
):
    return service.publish_question(current_user_id, payload)



# 🌟 接收用户点赞/踩的终极通道
@router.post("/answers/{answer_id}/feedback")
def submit_answer_feedback(
    answer_id: int,
    payload: FeedbackRequest,
    current_user_id: int = Depends(get_current_user_id),
):
    service = AnswerService()
    return service.submit_feedback(answer_id, current_user_id, payload.is_like)



@router.get("/{question_id}/feedbacks")
def get_my_feedbacks(
    question_id: int,
    current_user_id: int = Depends(get_current_user_id),
):
    service = AnswerService()
    return service.get_user_feedbacks(question_id, current_user_id)
