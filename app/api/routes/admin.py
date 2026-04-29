from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.auth_deps import AuthenticatedUser, get_admin_user
from app.api.deps import get_admin_service
from app.core.errors import AppError
from app.schemas.admin import (
    AdminCategoryListResponse,
    AdminCategoryMutationResponse,
    AdminCommentStatusResponse,
    AdminLoginLogListResponse,
    AdminOperationLogListResponse,
    AdminQuestionStatusResponse,
    AdminTagListResponse,
    AdminTagMutationResponse,
    AdminUserListResponse,
    AdminUserMutationResponse,
    CreateCategoryRequest,
    UpdateCommentStatusRequest,
    UpdateCategoryRequest,
    UpdateQuestionStatusRequest,
    UpdateTagRequest,
    UpdateUserRoleRequest,
    UpdateUserStatusRequest,
)
from app.services.admin_service import AdminService


router = APIRouter(prefix="/admin", tags=["admin"])


@router.get(
    "/categories",
    response_model=AdminCategoryListResponse,
    status_code=status.HTTP_200_OK,
)
def list_categories(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status_filter: str | None = Query(default=None, alias="status"),
    _: AuthenticatedUser = Depends(get_admin_user),
    service: AdminService = Depends(get_admin_service),
) -> AdminCategoryListResponse:
    try:
        return service.list_categories(
            page=page,
            page_size=page_size,
            status=status_filter,
        )
    except AppError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.post(
    "/categories",
    response_model=AdminCategoryMutationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_category(
    payload: CreateCategoryRequest,
    admin_user: AuthenticatedUser = Depends(get_admin_user),
    service: AdminService = Depends(get_admin_service),
) -> AdminCategoryMutationResponse:
    try:
        return service.create_category(
            admin_user_id=admin_user.user_id,
            category_name=payload.category_name,
            description=payload.description,
            status=payload.status,
        )
    except AppError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.patch(
    "/categories/{category_id}",
    response_model=AdminCategoryMutationResponse,
    status_code=status.HTTP_200_OK,
)
def update_category(
    category_id: int,
    payload: UpdateCategoryRequest,
    admin_user: AuthenticatedUser = Depends(get_admin_user),
    service: AdminService = Depends(get_admin_service),
) -> AdminCategoryMutationResponse:
    try:
        return service.update_category(
            admin_user_id=admin_user.user_id,
            category_id=category_id,
            category_name=payload.category_name,
            description=payload.description,
            status=payload.status,
        )
    except AppError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.get(
    "/tags",
    response_model=AdminTagListResponse,
    status_code=status.HTTP_200_OK,
)
def list_tags(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    source: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    keyword: str | None = Query(default=None),
    _: AuthenticatedUser = Depends(get_admin_user),
    service: AdminService = Depends(get_admin_service),
) -> AdminTagListResponse:
    try:
        return service.list_tags(
            page=page,
            page_size=page_size,
            source=source,
            status=status_filter,
            keyword=keyword,
        )
    except AppError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.patch(
    "/tags/{tag_id}",
    response_model=AdminTagMutationResponse,
    status_code=status.HTTP_200_OK,
)
def update_tag(
    tag_id: int,
    payload: UpdateTagRequest,
    admin_user: AuthenticatedUser = Depends(get_admin_user),
    service: AdminService = Depends(get_admin_service),
) -> AdminTagMutationResponse:
    try:
        return service.update_tag(
            admin_user_id=admin_user.user_id,
            tag_id=tag_id,
            tag_name=payload.tag_name,
            description=payload.description,
            status=payload.status,
        )
    except AppError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.get(
    "/users",
    response_model=AdminUserListResponse,
    status_code=status.HTTP_200_OK,
)
def list_users(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    role: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    _: AuthenticatedUser = Depends(get_admin_user),
    service: AdminService = Depends(get_admin_service),
) -> AdminUserListResponse:
    try:
        return service.list_users(
            page=page,
            page_size=page_size,
            role=role,
            status=status_filter,
        )
    except AppError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.get(
    "/logs/login",
    response_model=AdminLoginLogListResponse,
    status_code=status.HTTP_200_OK,
)
def list_login_logs(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    user_id: int | None = Query(default=None, gt=0),
    result: str | None = Query(default=None),
    _: AuthenticatedUser = Depends(get_admin_user),
    service: AdminService = Depends(get_admin_service),
) -> AdminLoginLogListResponse:
    try:
        return service.list_login_logs(
            page=page,
            page_size=page_size,
            user_id=user_id,
            result=result,
        )
    except AppError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.get(
    "/logs/operations",
    response_model=AdminOperationLogListResponse,
    status_code=status.HTTP_200_OK,
)
def list_operation_logs(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    user_id: int | None = Query(default=None, gt=0),
    op_type: str | None = Query(default=None),
    _: AuthenticatedUser = Depends(get_admin_user),
    service: AdminService = Depends(get_admin_service),
) -> AdminOperationLogListResponse:
    try:
        return service.list_operation_logs(
            page=page,
            page_size=page_size,
            user_id=user_id,
            op_type=op_type,
        )
    except AppError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.patch(
    "/users/{user_id}/status",
    response_model=AdminUserMutationResponse,
    status_code=status.HTTP_200_OK,
)
def update_user_status(
    user_id: int,
    payload: UpdateUserStatusRequest,
    admin_user: AuthenticatedUser = Depends(get_admin_user),
    service: AdminService = Depends(get_admin_service),
) -> AdminUserMutationResponse:
    try:
        return service.update_user_status(
            admin_user_id=admin_user.user_id,
            target_user_id=user_id,
            status=payload.status,
        )
    except AppError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.patch(
    "/users/{user_id}/role",
    response_model=AdminUserMutationResponse,
    status_code=status.HTTP_200_OK,
)
def update_user_role(
    user_id: int,
    payload: UpdateUserRoleRequest,
    admin_user: AuthenticatedUser = Depends(get_admin_user),
    service: AdminService = Depends(get_admin_service),
) -> AdminUserMutationResponse:
    try:
        return service.update_user_role(
            admin_user_id=admin_user.user_id,
            target_user_id=user_id,
            role=payload.role,
        )
    except AppError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.patch(
    "/questions/{question_id}/status",
    response_model=AdminQuestionStatusResponse,
    status_code=status.HTTP_200_OK,
)
def update_question_status(
    question_id: int,
    payload: UpdateQuestionStatusRequest,
    admin_user: AuthenticatedUser = Depends(get_admin_user),
    service: AdminService = Depends(get_admin_service),
) -> AdminQuestionStatusResponse:
    try:
        return service.update_question_status(
            admin_user_id=admin_user.user_id,
            question_id=question_id,
            status=payload.status,
        )
    except AppError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.delete(
    "/questions/{question_id}",
    response_model=AdminQuestionStatusResponse,
    status_code=status.HTTP_200_OK,
)
def delete_question(
    question_id: int,
    reason: str | None = Query(default=None, max_length=200),
    admin_user: AuthenticatedUser = Depends(get_admin_user),
    service: AdminService = Depends(get_admin_service),
) -> AdminQuestionStatusResponse:
    try:
        return service.delete_question(
            admin_user_id=admin_user.user_id,
            question_id=question_id,
            reason=reason,
        )
    except AppError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.patch(
    "/comments/{comment_id}/status",
    response_model=AdminCommentStatusResponse,
    status_code=status.HTTP_200_OK,
)
def update_comment_status(
    comment_id: int,
    payload: UpdateCommentStatusRequest,
    admin_user: AuthenticatedUser = Depends(get_admin_user),
    service: AdminService = Depends(get_admin_service),
) -> AdminCommentStatusResponse:
    try:
        return service.update_comment_status(
            admin_user_id=admin_user.user_id,
            comment_id=comment_id,
            status=payload.status,
        )
    except AppError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
