from datetime import datetime

from pydantic import Field

from app.schemas.base import APIModel


class CreateFavoriteRequest(APIModel):
    user_id: int | None = Field(default=None, gt=0)


class FavoriteRecordResponse(APIModel):
    favorite_id: int
    question_id: int
    user_id: int
    favorite_time: datetime
    favorite_count: int = Field(ge=0)


class FavoriteDeleteResponse(APIModel):
    question_id: int
    user_id: int
    favorite_count: int = Field(ge=0)
    deleted: bool = True
