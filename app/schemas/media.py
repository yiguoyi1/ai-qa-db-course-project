from datetime import datetime

from pydantic import Field

from app.schemas.base import APIModel


class MediaAssetItem(APIModel):
    media_id: int
    owner_type: str
    owner_id: int
    public_url: str
    mime_type: str
    file_size: int
    sort_order: int
    status: str
    create_time: datetime
    update_time: datetime


class AvatarMediaResponse(APIModel):
    media_id: int
    owner_type: str
    owner_id: int
    public_url: str
    mime_type: str
    file_size: int
    status: str
    create_time: datetime
    update_time: datetime


class AvatarDeleteResponse(APIModel):
    message: str


class QuestionImageListResponse(APIModel):
    question_id: int
    items: list[MediaAssetItem] = Field(default_factory=list)
    total: int = 0


class QuestionImageDeleteResponse(APIModel):
    question_id: int
    media_id: int
    message: str


class AnswerImageListResponse(APIModel):
    answer_id: int
    items: list[MediaAssetItem] = Field(default_factory=list)
    total: int = 0


class AnswerImageDeleteResponse(APIModel):
    answer_id: int
    media_id: int
    message: str
