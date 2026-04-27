from datetime import datetime

from pydantic import Field

from app.schemas.base import APIModel

from app.schemas.question import TagItem


class UserTagProfileItem(APIModel):
    tag_id: int
    tag_name: str
    weight: float
    update_time: datetime


class ProfileRebuildResponse(APIModel):
    user_id: int
    item_count: int = Field(ge=0)
    items: list[UserTagProfileItem] = Field(default_factory=list)


class RecommendationQuestionItem(APIModel):
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


class RecommendationItem(APIModel):
    rec_id: int
    rec_type: str
    rec_source: str | None = None
    rec_reason: str | None = None
    rec_score: float
    rec_time: datetime
    status: str
    question: RecommendationQuestionItem


class RecommendationListResponse(APIModel):
    user_id: int
    status: str
    total: int = Field(ge=0)
    items: list[RecommendationItem] = Field(default_factory=list)


class RecommendationGenerationResponse(APIModel):
    user_id: int
    requested_limit: int = Field(ge=1)
    active_count: int = Field(ge=0)
