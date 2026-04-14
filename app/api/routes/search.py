from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import get_search_service
from app.core.errors import AppError
from app.schemas.question import QuestionListResponse
from app.services.search_service import SearchService

# 🌟 1. 在文件顶部的 import 区域，把之前的验票保安请过来
from app.api.routes.questions import get_current_user_id

router = APIRouter(prefix="/search", tags=["search"])


@router.get(
    "/questions",
    response_model=QuestionListResponse,
    status_code=status.HTTP_200_OK,
)
def search_questions(
    q: str = Query(..., min_length=1),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=50),
    user_id: int | None = Query(default=None, gt=0),
    category_id: int | None = Query(default=None, gt=0),
    tag_id: int | None = Query(default=None, gt=0),
    status_filter: str | None = Query(default="OPEN", alias="status"),
    service: SearchService = Depends(get_search_service),
) -> QuestionListResponse:
    try:
        return service.search_questions(
            q=q,
            page=page,
            page_size=page_size,
            user_id=user_id,
            category_id=category_id,
            tag_id=tag_id,
            status=status_filter,
        )
    except AppError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc




# 🌟 2. 在文件最底部，新增拉取历史记录的大门
@router.get("/history", response_model=list[str])
def get_user_search_history(
    user_id: int = Depends(get_current_user_id), # 验票保安
    service: SearchService = Depends(get_search_service)
):
    return service.get_search_history(user_id)