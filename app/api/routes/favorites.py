from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.auth_deps import get_current_user_id, resolve_authenticated_user_id
from app.api.deps import get_favorite_service
from app.core.errors import AppError
from app.schemas.favorite import (
    CreateFavoriteRequest,
    FavoriteDeleteResponse,
    FavoriteRecordResponse,
)
from app.services.favorite_service import FavoriteService


router = APIRouter(prefix="/questions", tags=["favorites"])


@router.post(
    "/{question_id}/favorite",
    response_model=FavoriteRecordResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_favorite(
    question_id: int,
    payload: CreateFavoriteRequest,
    current_user_id: int = Depends(get_current_user_id),
    service: FavoriteService = Depends(get_favorite_service),
) -> FavoriteRecordResponse:
    try:
        normalized_payload = payload.model_copy(
            update={
                "user_id": resolve_authenticated_user_id(
                    current_user_id=current_user_id,
                    requested_user_id=payload.user_id,
                )
            }
        )
        return service.create_favorite(question_id=question_id, payload=normalized_payload)
    except AppError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.delete(
    "/{question_id}/favorite",
    response_model=FavoriteDeleteResponse,
    status_code=status.HTTP_200_OK,
)
def delete_favorite(
    question_id: int,
    user_id: int | None = Query(default=None, gt=0),
    current_user_id: int = Depends(get_current_user_id),
    service: FavoriteService = Depends(get_favorite_service),
) -> FavoriteDeleteResponse:
    try:
        return service.delete_favorite(
            question_id=question_id,
            user_id=resolve_authenticated_user_id(
                current_user_id=current_user_id,
                requested_user_id=user_id,
            ),
        )
    except AppError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
