from fastapi import APIRouter, Depends, HTTPException, status

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
    service: BrowseService = Depends(get_browse_service),
) -> BrowseRecordResponse:
    try:
        return service.create_browse_record(question_id=question_id, payload=payload)
    except AppError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
