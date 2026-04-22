from fastapi import APIRouter, Depends, HTTPException, status

from app.api.auth_deps import get_current_user_id, resolve_authenticated_user_id
from app.api.deps import get_browse_service
from app.core.errors import AppError
from app.schemas.browse import BrowseRecordResponse, CreateBrowseRecordRequest
from app.services.browse_service import BrowseService


router = APIRouter(prefix="/questions", tags=["browse"])


@router.post(
    "/{question_id}/browse",
    response_model=BrowseRecordResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_browse_record(
    question_id: int,
    payload: CreateBrowseRecordRequest,
    current_user_id: int = Depends(get_current_user_id),
    service: BrowseService = Depends(get_browse_service),
) -> BrowseRecordResponse:
    try:
        normalized_payload = payload.model_copy(
            update={
                "user_id": resolve_authenticated_user_id(
                    current_user_id=current_user_id,
                    requested_user_id=payload.user_id,
                )
            }
        )
        return service.create_browse_record(question_id=question_id, payload=normalized_payload)
    except AppError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
