from pydantic import BaseModel, Field


class CreateManualAnswerRequest(BaseModel):
    user_id: int | None = Field(default=None, gt=0)
    content: str = Field(min_length=1)
    confidence_score: float | None = Field(default=None, ge=0, le=100)
