from datetime import datetime

from pydantic import BaseModel, Field


class CreateBrowseRecordRequest(BaseModel):
    user_id: int = Field(gt=0)
    duration: int = Field(default=0, ge=0)
    click_depth: int = Field(default=1, ge=1)


class BrowseRecordResponse(BaseModel):
    history_id: int
    question_id: int
    user_id: int
    browse_time: datetime
    duration: int
    click_depth: int
    view_count: int = Field(ge=0)
