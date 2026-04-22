from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.auth_deps import ensure_path_user_access, get_current_user_id
from app.api.deps import get_user_center_service
from app.core.errors import AppError
from app.schemas.user_center import (
    UserAnswerListResponse,
    UserBrowseHistoryResponse,
    UserCenterProfileResponse,
    UserFavoriteListResponse,
    UserQuestionListResponse,
    UserSearchHistoryResponse,
)
from app.services.user_center_service import UserCenterService


router = APIRouter(prefix="/users", tags=["users"])


@router.get(
    "/{user_id}/profile",
    response_model=UserCenterProfileResponse,
    status_code=status.HTTP_200_OK,
)
def get_profile(
    user_id: int,
    current_user_id: int = Depends(get_current_user_id),
    service: UserCenterService = Depends(get_user_center_service),
) -> UserCenterProfileResponse:
    try:
        return service.get_profile(
            user_id=ensure_path_user_access(
                path_user_id=user_id,
                current_user_id=current_user_id,
            )
        )
    except AppError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.get(
    "/{user_id}/questions",
    response_model=UserQuestionListResponse,
    status_code=status.HTTP_200_OK,
)
def list_user_questions(
    user_id: int,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=50),
    current_user_id: int = Depends(get_current_user_id),
    service: UserCenterService = Depends(get_user_center_service),
) -> UserQuestionListResponse:
    try:
        return service.list_questions(
            user_id=ensure_path_user_access(
                path_user_id=user_id,
                current_user_id=current_user_id,
            ),
            page=page,
            page_size=page_size,
        )
    except AppError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.get(
    "/{user_id}/answers",
    response_model=UserAnswerListResponse,
    status_code=status.HTTP_200_OK,
)
def list_user_answers(
    user_id: int,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=50),
    current_user_id: int = Depends(get_current_user_id),
    service: UserCenterService = Depends(get_user_center_service),
) -> UserAnswerListResponse:
    try:
        return service.list_answers(
            user_id=ensure_path_user_access(
                path_user_id=user_id,
                current_user_id=current_user_id,
            ),
            page=page,
            page_size=page_size,
        )
    except AppError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.get(
    "/{user_id}/favorites",
    response_model=UserFavoriteListResponse,
    status_code=status.HTTP_200_OK,
)
def list_user_favorites(
    user_id: int,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=50),
    current_user_id: int = Depends(get_current_user_id),
    service: UserCenterService = Depends(get_user_center_service),
) -> UserFavoriteListResponse:
    try:
        return service.list_favorites(
            user_id=ensure_path_user_access(
                path_user_id=user_id,
                current_user_id=current_user_id,
            ),
            page=page,
            page_size=page_size,
        )
    except AppError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.get(
    "/{user_id}/browse-history",
    response_model=UserBrowseHistoryResponse,
    status_code=status.HTTP_200_OK,
)
def list_user_browse_history(
    user_id: int,
    limit: int = Query(default=8, ge=1, le=50),
    current_user_id: int = Depends(get_current_user_id),
    service: UserCenterService = Depends(get_user_center_service),
) -> UserBrowseHistoryResponse:
    try:
        return service.list_browse_history(
            user_id=ensure_path_user_access(
                path_user_id=user_id,
                current_user_id=current_user_id,
            ),
            limit=limit,
        )
    except AppError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.get(
    "/{user_id}/search-history",
    response_model=UserSearchHistoryResponse,
    status_code=status.HTTP_200_OK,
)
def list_user_search_history(
    user_id: int,
    limit: int = Query(default=8, ge=1, le=50),
    current_user_id: int = Depends(get_current_user_id),
    service: UserCenterService = Depends(get_user_center_service),
) -> UserSearchHistoryResponse:
    try:
        return service.list_search_history(
            user_id=ensure_path_user_access(
                path_user_id=user_id,
                current_user_id=current_user_id,
            ),
            limit=limit,
        )
    except AppError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
