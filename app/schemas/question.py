from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.media import MediaAssetItem


class AskQuestionRequest(BaseModel):
    user_id: int | None = Field(default=None, gt=0)
    category_id: int = Field(gt=0)
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1)
    tag_ids: list[int] = Field(default_factory=list)


class TagItem(BaseModel):
    tag_id: int
    tag_name: str


class AnswerItem(BaseModel):
    answer_id: int
    user_id: int | None = None
    answer_type: str
    provider_name: str | None = None
    author_username: str | None = None
    author_nickname: str | None = None
    author_avatar_url: str | None = None
    content: str
    generate_time: datetime
    model_name: str | None = None
    confidence_score: float | None = None
    like_count: int
    dislike_count: int
    avg_rating: float | None = None
    is_accepted: bool = False
    images: list[MediaAssetItem] = Field(default_factory=list)


class QuestionSummaryItem(BaseModel):
    question_id: int
    user_id: int
    category_id: int
    title: str
    ask_time: datetime
    status: str
    view_count: int
    favorite_count: int
    answer_count: int
    is_favorited: bool = False
    tags: list[TagItem] = Field(default_factory=list)
    username: str | None = None
    author_avatar_url: str | None = None


class QuestionListResponse(BaseModel):
    items: list[QuestionSummaryItem] = Field(default_factory=list)
    page: int = Field(ge=1)
    page_size: int = Field(ge=1)
    total: int = Field(ge=0)


class QuestionDetailResponse(BaseModel):
    question_id: int
    user_id: int
    category_id: int
    title: str
    content: str
    ask_time: datetime
    status: str
    accepted_answer_id: int | None = None
    view_count: int
    favorite_count: int
    answer_count: int
    is_favorited: bool = False
    tags: list[TagItem] = Field(default_factory=list)
    images: list[MediaAssetItem] = Field(default_factory=list)
    answers: list[AnswerItem] = Field(default_factory=list)
    username: str | None = None
    author_avatar_url: str | None = None


class QuestionCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1)
