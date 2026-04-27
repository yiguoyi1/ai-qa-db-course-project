from datetime import datetime
from typing import Literal

from pydantic import Field

from app.schemas.base import APIModel


class SaveAnswerFeedbackRequest(APIModel):
    user_id: int | None = Field(default=None, gt=0)
    is_like: Literal["Y", "N"]
    rating: float | None = Field(default=None, ge=0, le=5)
    comment_text: str | None = Field(default=None, max_length=500)


class AnswerFeedbackResponse(APIModel):
    feedback_id: int | None = None
    answer_id: int
    user_id: int
    is_like: str | None = None
    rating: float | None = None
    comment_text: str | None = None
    feedback_time: datetime | None = None
    like_count: int = Field(ge=0)
    dislike_count: int = Field(ge=0)
    avg_rating: float | None = None
    operation: Literal["CREATED", "UPDATED", "DELETED"]
