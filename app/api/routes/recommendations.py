from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.auth_deps import ensure_path_user_access, get_current_user_id
from app.api.deps import get_recommendation_service
from app.core.errors import AppError
from app.schemas.recommendation import (
    ProfileRebuildResponse,
    RecommendationGenerationResponse,
    RecommendationListResponse,
)
from app.services.recommendation_service import RecommendationService


router = APIRouter(prefix="/users", tags=["recommendations"])


@router.post(
    "/{user_id}/profile/rebuild",
    response_model=ProfileRebuildResponse,
    status_code=status.HTTP_200_OK,
)
def rebuild_profile(
    user_id: int,
    current_user_id: int = Depends(get_current_user_id),
    service: RecommendationService = Depends(get_recommendation_service),
) -> ProfileRebuildResponse:
    try:
        return service.rebuild_profile(
            user_id=ensure_path_user_access(
                path_user_id=user_id,
                current_user_id=current_user_id,
            )
        )
    except AppError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.post(
    "/{user_id}/recommendations/generate",
    response_model=RecommendationGenerationResponse,
    status_code=status.HTTP_200_OK,
)
def generate_recommendations(
    user_id: int,
    limit: int = Query(default=10, ge=1, le=50),
    current_user_id: int = Depends(get_current_user_id),
    service: RecommendationService = Depends(get_recommendation_service),
) -> RecommendationGenerationResponse:
    try:
        return service.generate_recommendations(
            user_id=ensure_path_user_access(
                path_user_id=user_id,
                current_user_id=current_user_id,
            ),
            limit=limit,
        )
    except AppError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.get(
    "/{user_id}/recommendations",
    response_model=RecommendationListResponse,
    status_code=status.HTTP_200_OK,
)
def list_recommendations(
    user_id: int,
    status_filter: str = Query(default="ACTIVE", alias="status"),
    current_user_id: int = Depends(get_current_user_id),
    service: RecommendationService = Depends(get_recommendation_service),
) -> RecommendationListResponse:
    try:
        return service.list_recommendations(
            user_id=ensure_path_user_access(
                path_user_id=user_id,
                current_user_id=current_user_id,
            ),
            status=status_filter,
        )
    except AppError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
