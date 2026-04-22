from fastapi import APIRouter, Depends, HTTPException, status

from app.api.auth_deps import get_current_user_id, resolve_authenticated_user_id
from app.api.deps import get_comment_service
from app.core.errors import AppError
from app.schemas.comment import (
    CommentItem,
    CommentTreeResponse,
    CreateCommentRequest,
    DeleteCommentResponse,
)
from app.services.comment_service import CommentService


router = APIRouter(tags=["comments"])


@router.post(
    "/answers/{answer_id}/comments",
    response_model=CommentItem,
    status_code=status.HTTP_201_CREATED,
)
def create_comment(
    answer_id: int,
    payload: CreateCommentRequest,
    current_user_id: int = Depends(get_current_user_id),
    service: CommentService = Depends(get_comment_service),
) -> CommentItem:
    try:
        normalized_payload = payload.model_copy(
            update={
                "user_id": resolve_authenticated_user_id(
                    current_user_id=current_user_id,
                    requested_user_id=payload.user_id,
                )
            }
        )
        return service.create_comment(answer_id=answer_id, payload=normalized_payload)
    except AppError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.get(
    "/answers/{answer_id}/comments",
    response_model=CommentTreeResponse,
)
def list_comments(
    answer_id: int,
    service: CommentService = Depends(get_comment_service),
) -> CommentTreeResponse:
    try:
        return service.list_comments(answer_id=answer_id)
    except AppError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.delete(
    "/comments/{comment_id}",
    response_model=DeleteCommentResponse,
)
def delete_comment(
    comment_id: int,
    user_id: int | None = None,
    current_user_id: int = Depends(get_current_user_id),
    service: CommentService = Depends(get_comment_service),
) -> DeleteCommentResponse:
    try:
        return service.delete_comment(
            comment_id=comment_id,
            user_id=resolve_authenticated_user_id(
                current_user_id=current_user_id,
                requested_user_id=user_id,
            ),
        )
    except AppError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
