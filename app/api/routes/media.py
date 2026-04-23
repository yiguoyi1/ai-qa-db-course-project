from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile, status

from app.api.auth_deps import AuthenticatedUser, get_current_user
from app.api.deps import get_media_service
from app.core.errors import AppError
from app.schemas.media import (
    AnswerImageDeleteResponse,
    AnswerImageListResponse,
    AvatarDeleteResponse,
    AvatarMediaResponse,
    QuestionImageDeleteResponse,
    QuestionImageListResponse,
)
from app.services.media_service import MediaService


router = APIRouter(tags=["media"])


@router.get(
    "/media/files/{file_name}",
    status_code=status.HTTP_200_OK,
)
def get_media_file(
    file_name: str,
    service: MediaService = Depends(get_media_service),
) -> Response:
    try:
        content, mime_type = service.get_media_content(file_name=file_name)
        return Response(content=content, media_type=mime_type)
    except AppError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.post(
    "/users/me/avatar",
    response_model=AvatarMediaResponse,
    status_code=status.HTTP_200_OK,
)
async def upload_current_user_avatar(
    file: UploadFile = File(...),
    current_user: AuthenticatedUser = Depends(get_current_user),
    service: MediaService = Depends(get_media_service),
) -> AvatarMediaResponse:
    try:
        content = await file.read()
        return service.upload_current_user_avatar(
            user_id=current_user.user_id,
            original_file_name=file.filename,
            mime_type=file.content_type,
            content=content,
        )
    except AppError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    finally:
        await file.close()


@router.get(
    "/users/me/avatar",
    response_model=AvatarMediaResponse,
    status_code=status.HTTP_200_OK,
)
def get_current_user_avatar(
    current_user: AuthenticatedUser = Depends(get_current_user),
    service: MediaService = Depends(get_media_service),
) -> AvatarMediaResponse:
    try:
        return service.get_current_user_avatar(user_id=current_user.user_id)
    except AppError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.delete(
    "/users/me/avatar",
    response_model=AvatarDeleteResponse,
    status_code=status.HTTP_200_OK,
)
def delete_current_user_avatar(
    current_user: AuthenticatedUser = Depends(get_current_user),
    service: MediaService = Depends(get_media_service),
) -> AvatarDeleteResponse:
    try:
        return service.delete_current_user_avatar(user_id=current_user.user_id)
    except AppError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.post(
    "/questions/{question_id}/images",
    response_model=QuestionImageListResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_question_image(
    question_id: int,
    file: UploadFile = File(...),
    current_user: AuthenticatedUser = Depends(get_current_user),
    service: MediaService = Depends(get_media_service),
) -> QuestionImageListResponse:
    try:
        content = await file.read()
        return service.upload_question_image(
            user_id=current_user.user_id,
            question_id=question_id,
            original_file_name=file.filename,
            mime_type=file.content_type,
            content=content,
        )
    except AppError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    finally:
        await file.close()


@router.get(
    "/questions/{question_id}/images",
    response_model=QuestionImageListResponse,
    status_code=status.HTTP_200_OK,
)
def list_question_images(
    question_id: int,
    service: MediaService = Depends(get_media_service),
) -> QuestionImageListResponse:
    try:
        return service.list_question_images(question_id=question_id)
    except AppError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.delete(
    "/questions/{question_id}/images/{media_id}",
    response_model=QuestionImageDeleteResponse,
    status_code=status.HTTP_200_OK,
)
def delete_question_image(
    question_id: int,
    media_id: int,
    current_user: AuthenticatedUser = Depends(get_current_user),
    service: MediaService = Depends(get_media_service),
) -> QuestionImageDeleteResponse:
    try:
        return service.delete_question_image(
            user_id=current_user.user_id,
            question_id=question_id,
            media_id=media_id,
        )
    except AppError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.post(
    "/answers/{answer_id}/images",
    response_model=AnswerImageListResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_answer_image(
    answer_id: int,
    file: UploadFile = File(...),
    current_user: AuthenticatedUser = Depends(get_current_user),
    service: MediaService = Depends(get_media_service),
) -> AnswerImageListResponse:
    try:
        content = await file.read()
        return service.upload_answer_image(
            user_id=current_user.user_id,
            answer_id=answer_id,
            original_file_name=file.filename,
            mime_type=file.content_type,
            content=content,
        )
    except AppError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    finally:
        await file.close()


@router.get(
    "/answers/{answer_id}/images",
    response_model=AnswerImageListResponse,
    status_code=status.HTTP_200_OK,
)
def list_answer_images(
    answer_id: int,
    service: MediaService = Depends(get_media_service),
) -> AnswerImageListResponse:
    try:
        return service.list_answer_images(answer_id=answer_id)
    except AppError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.delete(
    "/answers/{answer_id}/images/{media_id}",
    response_model=AnswerImageDeleteResponse,
    status_code=status.HTTP_200_OK,
)
def delete_answer_image(
    answer_id: int,
    media_id: int,
    current_user: AuthenticatedUser = Depends(get_current_user),
    service: MediaService = Depends(get_media_service),
) -> AnswerImageDeleteResponse:
    try:
        return service.delete_answer_image(
            user_id=current_user.user_id,
            answer_id=answer_id,
            media_id=media_id,
        )
    except AppError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
