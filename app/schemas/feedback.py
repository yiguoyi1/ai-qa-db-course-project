from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class SaveAnswerFeedbackRequest(BaseModel):
    user_id: int = Field(gt=0)
    is_like: Literal["Y", "N"]
    rating: float | None = Field(default=None, ge=0, le=5)
    comment_text: str | None = Field(default=None, max_length=500)


class AnswerFeedbackResponse(BaseModel):
    feedback_id: int
    answer_id: int
    user_id: int
    is_like: str
    rating: float | None = None
    comment_text: str | None = None
    feedback_time: datetime
    like_count: int = Field(ge=0)
    dislike_count: int = Field(ge=0)
    avg_rating: float | None = None
    operation: Literal["CREATED", "UPDATED"]
