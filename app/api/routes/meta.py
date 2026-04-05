from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_meta_service
from app.core.errors import AppError
from app.schemas.meta import CategoryListResponse, TagListResponse
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
    service: MetaService = Depends(get_meta_service),
) -> TagListResponse:
    try:
        return service.list_tags()
    except AppError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
