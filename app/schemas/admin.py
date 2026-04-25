from datetime import datetime

from pydantic import Field

from app.schemas.base import APIModel


class AdminUserItem(APIModel):
    user_id: int
    username: str
    nickname: str | None = None
    email: str | None = None
    phone: str | None = None
    role: str
    status: str
    register_time: datetime
    last_login_time: datetime | None = None


class AdminUserListResponse(APIModel):
    items: list[AdminUserItem] = Field(default_factory=list)
    page: int = Field(ge=1)
    page_size: int = Field(ge=1)
    total: int = Field(ge=0)


class UpdateUserStatusRequest(APIModel):
    status: str = Field(min_length=1, max_length=20)


class UpdateUserRoleRequest(APIModel):
    role: str = Field(min_length=1, max_length=20)


class UpdateQuestionStatusRequest(APIModel):
    status: str = Field(min_length=1, max_length=20)


class UpdateCommentStatusRequest(APIModel):
    status: str = Field(min_length=1, max_length=20)


class AdminUserMutationResponse(APIModel):
    user_id: int
    username: str
    role: str
    status: str
    message: str


class AdminCategoryItem(APIModel):
    category_id: int
    category_name: str
    description: str | None = None
    status: str


class AdminCategoryListResponse(APIModel):
    items: list[AdminCategoryItem] = Field(default_factory=list)
    page: int = Field(ge=1)
    page_size: int = Field(ge=1)
    total: int = Field(ge=0)


class CreateCategoryRequest(APIModel):
    category_name: str = Field(min_length=1, max_length=50)
    description: str | None = Field(default=None, max_length=200)
    status: str = Field(default="ACTIVE", min_length=1, max_length=20)


class UpdateCategoryRequest(APIModel):
    category_name: str | None = Field(default=None, min_length=1, max_length=50)
    description: str | None = Field(default=None, max_length=200)
    status: str | None = Field(default=None, min_length=1, max_length=20)


class AdminCategoryMutationResponse(APIModel):
    category_id: int
    category_name: str
    description: str | None = None
    status: str
    message: str


class AdminQuestionStatusResponse(APIModel):
    question_id: int
    status: str
    message: str


class AdminCommentStatusResponse(APIModel):
    comment_id: int
    status: str
    message: str


class AdminLoginLogItem(APIModel):
    log_id: int
    user_id: int
    username: str | None = None
    login_time: datetime
    ip_address: str | None = None
    result: str


class AdminLoginLogListResponse(APIModel):
    items: list[AdminLoginLogItem] = Field(default_factory=list)
    page: int = Field(ge=1)
    page_size: int = Field(ge=1)
    total: int = Field(ge=0)


class AdminOperationLogItem(APIModel):
    op_id: int
    user_id: int
    username: str | None = None
    op_type: str
    op_content: str
    op_time: datetime


class AdminOperationLogListResponse(APIModel):
    items: list[AdminOperationLogItem] = Field(default_factory=list)
    page: int = Field(ge=1)
    page_size: int = Field(ge=1)
    total: int = Field(ge=0)
