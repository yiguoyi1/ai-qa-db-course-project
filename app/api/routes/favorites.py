from fastapi import APIRouter, Depends, HTTPException, Query, status

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
    service: FavoriteService = Depends(get_favorite_service),
) -> FavoriteRecordResponse:
    try:
        return service.create_favorite(question_id=question_id, payload=payload)
    except AppError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.delete(
    "/{question_id}/favorite",
    response_model=FavoriteDeleteResponse,
    status_code=status.HTTP_200_OK,
)
def delete_favorite(
    question_id: int,
    user_id: int = Query(..., gt=0),
    service: FavoriteService = Depends(get_favorite_service),
) -> FavoriteDeleteResponse:
    try:
        return service.delete_favorite(question_id=question_id, user_id=user_id)
    except AppError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
