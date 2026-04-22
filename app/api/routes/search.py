from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.auth_deps import (
    get_current_user_id,
    get_optional_current_user_id,
    resolve_tracking_user_id,
)
from app.api.deps import get_search_service
from app.core.errors import AppError
from app.schemas.question import QuestionListResponse
from app.services.search_service import SearchService

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
    current_user_id: int | None = Depends(get_optional_current_user_id),
    service: SearchService = Depends(get_search_service),
) -> QuestionListResponse:
    try:
        return service.search_questions(
            q=q,
            page=page,
            page_size=page_size,
            user_id=resolve_tracking_user_id(
                current_user_id=current_user_id,
                requested_user_id=user_id,
            ),
            category_id=category_id,
            tag_id=tag_id,
            status=status_filter,
        )
    except AppError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc




# 🌟 2. 在文件最底部，新增拉取历史记录的大门
@router.get("/history", response_model=list[str])
def get_user_search_history(
    current_user_id: int = Depends(get_current_user_id),
    service: SearchService = Depends(get_search_service),
):
    return service.get_search_history(current_user_id)
