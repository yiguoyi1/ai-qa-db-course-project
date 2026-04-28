from pydantic import Field

from app.schemas.base import APIModel


class CreateManualAnswerRequest(APIModel):
    user_id: int | None = Field(default=None, gt=0)
    content: str = Field(min_length=1, max_length=10000)
    confidence_score: float | None = Field(default=None, ge=0, le=100)


class AcceptAnswerRequest(APIModel):
    answer_id: int = Field(gt=0)
