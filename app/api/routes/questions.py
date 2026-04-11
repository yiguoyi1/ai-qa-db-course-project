from fastapi import APIRouter, Depends, HTTPException, Query, status, Header
from jose import jwt # 👈 用于解析 Token

from app.services.auth_service import SECRET_KEY, ALGORITHM # 👈 引入解密钥匙
from app.schemas.question import QuestionCreate # 👈 引入新标准
from app.api.deps import get_question_service
from app.core.errors import AppError
from app.schemas.question import (
    AskQuestionRequest,
    QuestionDetailResponse,
    QuestionListResponse,
)
from app.services.question_service import QuestionService
from app.schemas.question import QuestionListItem

from pydantic import BaseModel
from app.services.answer_service import AnswerService
from app.schemas.answer import CreateManualAnswerRequest

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


@router.get("", response_model=list[QuestionListItem])
def list_questions(question_service: QuestionService = Depends(get_question_service)):
    return question_service.get_questions()

# 🌟 验票保安：负责把 Token 还原成 user_id
def get_current_user_id(authorization: str = Header(...)) -> int:
    try:
        token = authorization.split(" ")[1]
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return int(payload.get("sub"))
    except:
        raise HTTPException(status_code=401, detail="房卡无效或已过期，请重新登录")

# 🌟 终于！开设接收纯社区发帖的 POST 大门 🌟
@router.post("")
def create_community_question(
    payload: QuestionCreate,
    user_id: int = Depends(get_current_user_id), # 先过验票保安
    service: QuestionService = Depends(get_question_service)
):
    return service.publish_question(user_id, payload)

