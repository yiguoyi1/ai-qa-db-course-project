from datetime import datetime

from pydantic import BaseModel, Field


class AdminUserItem(BaseModel):
    user_id: int
    username: str
    nickname: str | None = None
    email: str | None = None
    phone: str | None = None
    role: str
    status: str
    register_time: datetime
    last_login_time: datetime | None = None


class AdminUserListResponse(BaseModel):
    items: list[AdminUserItem] = Field(default_factory=list)
    page: int = Field(ge=1)
    page_size: int = Field(ge=1)
    total: int = Field(ge=0)


class UpdateUserStatusRequest(BaseModel):
    status: str = Field(min_length=1, max_length=20)


class UpdateUserRoleRequest(BaseModel):
    role: str = Field(min_length=1, max_length=20)


class UpdateQuestionStatusRequest(BaseModel):
    status: str = Field(min_length=1, max_length=20)


class UpdateCommentStatusRequest(BaseModel):
    status: str = Field(min_length=1, max_length=20)


class AdminUserMutationResponse(BaseModel):
    user_id: int
    username: str
    role: str
    status: str
    message: str


class AdminCategoryItem(BaseModel):
    category_id: int
    category_name: str
    description: str | None = None
    status: str


class AdminCategoryListResponse(BaseModel):
    items: list[AdminCategoryItem] = Field(default_factory=list)
    page: int = Field(ge=1)
    page_size: int = Field(ge=1)
    total: int = Field(ge=0)


class CreateCategoryRequest(BaseModel):
    category_name: str = Field(min_length=1, max_length=50)
    description: str | None = Field(default=None, max_length=200)
    status: str = Field(default="ACTIVE", min_length=1, max_length=20)


class UpdateCategoryRequest(BaseModel):
    category_name: str | None = Field(default=None, min_length=1, max_length=50)
    description: str | None = Field(default=None, max_length=200)
    status: str | None = Field(default=None, min_length=1, max_length=20)


class AdminCategoryMutationResponse(BaseModel):
    category_id: int
    category_name: str
    description: str | None = None
    status: str
    message: str


class AdminQuestionStatusResponse(BaseModel):
    question_id: int
    status: str
    message: str


class AdminCommentStatusResponse(BaseModel):
    comment_id: int
    status: str
    message: str


class AdminLoginLogItem(BaseModel):
    log_id: int
    user_id: int
    username: str | None = None
    login_time: datetime
    ip_address: str | None = None
    result: str


class AdminLoginLogListResponse(BaseModel):
    items: list[AdminLoginLogItem] = Field(default_factory=list)
    page: int = Field(ge=1)
    page_size: int = Field(ge=1)
    total: int = Field(ge=0)


class AdminOperationLogItem(BaseModel):
    op_id: int
    user_id: int
    username: str | None = None
    op_type: str
    op_content: str
    op_time: datetime


class AdminOperationLogListResponse(BaseModel):
    items: list[AdminOperationLogItem] = Field(default_factory=list)
    page: int = Field(ge=1)
    page_size: int = Field(ge=1)
    total: int = Field(ge=0)
