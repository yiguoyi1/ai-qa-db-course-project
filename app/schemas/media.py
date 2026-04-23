from datetime import datetime

from pydantic import BaseModel, Field


class MediaAssetItem(BaseModel):
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


class AvatarMediaResponse(BaseModel):
    media_id: int
    owner_type: str
    owner_id: int
    public_url: str
    mime_type: str
    file_size: int
    status: str
    create_time: datetime
    update_time: datetime


class AvatarDeleteResponse(BaseModel):
    message: str


class QuestionImageListResponse(BaseModel):
    question_id: int
    items: list[MediaAssetItem] = Field(default_factory=list)
    total: int = 0


class QuestionImageDeleteResponse(BaseModel):
    question_id: int
    media_id: int
    message: str


class AnswerImageListResponse(BaseModel):
    answer_id: int
    items: list[MediaAssetItem] = Field(default_factory=list)
    total: int = 0


class AnswerImageDeleteResponse(BaseModel):
    answer_id: int
    media_id: int
    message: str
