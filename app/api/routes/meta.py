from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import get_meta_service
from app.core.errors import AppError
from app.schemas.meta import CategoryListResponse, TagListResponse, TagSuggestionResponse
from app.services.meta_service import MetaService


router = APIRouter(tags=["meta"])


@router.get(
    "/categories",
    response_model=CategoryListResponse,
    status_code=status.HTTP_200_OK,
)
def list_categories(
    service: MetaService = Depends(get_meta_service),
) -> CategoryListResponse:
    try:
        return service.list_categories()
    except AppError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.get(
    "/tags",
    response_model=TagListResponse,
    status_code=status.HTTP_200_OK,
)
def list_tags(
    limit: int | None = Query(default=None, ge=1, le=200),
    service: MetaService = Depends(get_meta_service),
) -> TagListResponse:
    try:
        return service.list_tags(limit=limit)
    except AppError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.get(
    "/tags/suggestions",
    response_model=TagSuggestionResponse,
    status_code=status.HTTP_200_OK,
)
def suggest_tags(
    keyword: str | None = Query(default=None, max_length=50),
    limit: int = Query(default=10, ge=1, le=20),
    service: MetaService = Depends(get_meta_service),
) -> TagSuggestionResponse:
    try:
        return service.suggest_tags(keyword=keyword, limit=limit)
    except AppError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
