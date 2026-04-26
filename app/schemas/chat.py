from datetime import datetime

from pydantic import Field

from app.schemas.base import APIModel


class CreateFollowUpTurnRequest(APIModel):
    session_id: int | None = Field(default=None, gt=0)
    content: str = Field(min_length=1, max_length=4000)


class ChatMessageItem(APIModel):
    message_id: int
    session_id: int
    sender_type: str
    content: str
    send_time: datetime
    model_name: str | None = None


class ChatSessionItem(APIModel):
    session_id: int
    user_id: int
    username: str | None = None
    nickname: str | None = None
    question_id: int
    seed_answer_id: int
    status: str
    start_time: datetime
    end_time: datetime | None = None
    message_count: int = Field(ge=0, default=0)
    last_message_time: datetime | None = None


class ChatSessionDetailResponse(APIModel):
    session: ChatSessionItem
    messages: list[ChatMessageItem] = Field(default_factory=list)


class ChatSessionListResponse(APIModel):
    question_id: int
    seed_answer_id: int
    item_count: int = Field(ge=0)
    items: list[ChatSessionItem] = Field(default_factory=list)
