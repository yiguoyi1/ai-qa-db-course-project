from datetime import datetime

from pydantic import Field

from app.schemas.base import APIModel

from app.schemas.question import QuestionSummaryItem, TagItem


class UserCenterProfileResponse(APIModel):
    user_id: int
    username: str
    nickname: str | None = None
    email: str | None = None
    phone: str | None = None
    avatar_media_id: int | None = None
    avatar_url: str | None = None
    role: str
    status: str
    register_time: datetime
    last_login_time: datetime | None = None
    question_count: int = Field(ge=0)
    answer_count: int = Field(ge=0)
    favorite_count: int = Field(ge=0)
    accepted_answer_count: int = Field(ge=0)


class UpdateCurrentUserProfileRequest(APIModel):
    nickname: str | None = Field(default=None, max_length=50)
    email: str | None = Field(default=None, max_length=100)
    phone: str | None = Field(default=None, max_length=20)


class UserQuestionListResponse(APIModel):
    user_id: int
    page: int = Field(ge=1)
    page_size: int = Field(ge=1)
    total: int = Field(ge=0)
    items: list[QuestionSummaryItem] = Field(default_factory=list)


class UserAnswerQuestionItem(APIModel):
    question_id: int
    title: str
    status: str
    tags: list[TagItem] = Field(default_factory=list)


class UserAnswerSummaryItem(APIModel):
    answer_id: int
    question: UserAnswerQuestionItem
    answer_type: str
    provider_name: str | None = None
    model_name: str | None = None
    content: str
    generate_time: datetime
    confidence_score: float | None = None
    like_count: int = Field(ge=0)
    dislike_count: int = Field(ge=0)
    avg_rating: float | None = None
    is_accepted: bool = False


class UserAnswerListResponse(APIModel):
    user_id: int
    page: int = Field(ge=1)
    page_size: int = Field(ge=1)
    total: int = Field(ge=0)
    items: list[UserAnswerSummaryItem] = Field(default_factory=list)


class UserFavoriteQuestionItem(APIModel):
    question_id: int
    user_id: int
    category_id: int
    title: str
    ask_time: datetime
    status: str
    view_count: int
    favorite_count: int
    answer_count: int
    username: str | None = None
    author_nickname: str | None = None
    author_avatar_url: str | None = None
    tags: list[TagItem] = Field(default_factory=list)


class UserFavoriteItem(APIModel):
    favorite_id: int
    favorite_time: datetime
    question: UserFavoriteQuestionItem


class UserFavoriteListResponse(APIModel):
    user_id: int
    page: int = Field(ge=1)
    page_size: int = Field(ge=1)
    total: int = Field(ge=0)
    items: list[UserFavoriteItem] = Field(default_factory=list)


class UserBrowseHistoryItem(APIModel):
    history_id: int
    question_id: int
    question_title: str
    question_status: str
    browse_time: datetime
    duration: int = Field(ge=0)
    click_depth: int = Field(ge=1)


class UserBrowseHistoryResponse(APIModel):
    user_id: int
    limit: int = Field(ge=1)
    item_count: int = Field(ge=0)
    items: list[UserBrowseHistoryItem] = Field(default_factory=list)


class UserSearchHistoryItem(APIModel):
    keyword: str
    last_search_time: datetime


class UserSearchHistoryResponse(APIModel):
    user_id: int
    limit: int = Field(ge=1)
    item_count: int = Field(ge=0)
    items: list[UserSearchHistoryItem] = Field(default_factory=list)
