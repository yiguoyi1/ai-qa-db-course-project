from fastapi import APIRouter, Depends, HTTPException, status

from app.api.auth_deps import get_current_user_id
from app.api.deps import get_chat_service
from app.core.errors import AppError
from app.schemas.chat import (
    ChatSessionDetailResponse,
    ChatSessionListResponse,
    CreateFollowUpTurnRequest,
)
from app.services.chat_service import ChatService


router = APIRouter(tags=["chat"])


@router.post(
    "/questions/{question_id}/answers/{answer_id}/follow-up",
    response_model=ChatSessionDetailResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_follow_up_turn(
    question_id: int,
    answer_id: int,
    payload: CreateFollowUpTurnRequest,
    current_user_id: int = Depends(get_current_user_id),
    service: ChatService = Depends(get_chat_service),
) -> ChatSessionDetailResponse:
    try:
        return service.create_follow_up_turn(
            question_id=question_id,
            answer_id=answer_id,
            current_user_id=current_user_id,
            payload=payload,
        )
    except AppError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.get(
    "/questions/{question_id}/answers/{answer_id}/follow-up-sessions",
    response_model=ChatSessionListResponse,
    status_code=status.HTTP_200_OK,
)
def list_follow_up_sessions(
    question_id: int,
    answer_id: int,
    current_user_id: int = Depends(get_current_user_id),
    service: ChatService = Depends(get_chat_service),
) -> ChatSessionListResponse:
    try:
        return service.list_sessions_by_anchor(
            question_id=question_id,
            answer_id=answer_id,
            current_user_id=current_user_id,
        )
    except AppError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.get(
    "/chat/sessions/{session_id}",
    response_model=ChatSessionDetailResponse,
    status_code=status.HTTP_200_OK,
)
def get_chat_session_detail(
    session_id: int,
    current_user_id: int = Depends(get_current_user_id),
    service: ChatService = Depends(get_chat_service),
) -> ChatSessionDetailResponse:
    try:
        return service.get_session_detail(
            session_id=session_id,
            current_user_id=current_user_id,
        )
    except AppError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
