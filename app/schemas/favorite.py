from datetime import datetime

from pydantic import BaseModel, Field


class CreateFavoriteRequest(BaseModel):
    user_id: int = Field(gt=0)


class FavoriteRecordResponse(BaseModel):
    favorite_id: int
    question_id: int
    user_id: int
    favorite_time: datetime
    favorite_count: int = Field(ge=0)


class FavoriteDeleteResponse(BaseModel):
    question_id: int
    user_id: int
    favorite_count: int = Field(ge=0)
    deleted: bool = True
