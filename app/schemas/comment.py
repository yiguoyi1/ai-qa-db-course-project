from __future__ import annotations

from datetime import datetime

from pydantic import Field

from app.schemas.base import APIModel


class CreateCommentRequest(APIModel):
    user_id: int | None = Field(default=None, gt=0)
    content: str = Field(min_length=1)
    parent_comment_id: int | None = Field(default=None, gt=0)


class DeleteCommentResponse(APIModel):
    comment_id: int
    user_id: int
    status: str
    deleted: bool


class CommentItem(APIModel):
    comment_id: int
    answer_id: int
    user_id: int
    parent_comment_id: int | None = None
    root_comment_id: int | None = None
    reply_to_user_id: int | None = None
    comment_level: int = Field(ge=1)
    status: str
    content: str
    reply_count: int = Field(ge=0)
    create_time: datetime
    update_time: datetime
    author_username: str | None = None
    author_nickname: str | None = None
    reply_to_username: str | None = None
    reply_to_nickname: str | None = None
    children: list["CommentItem"] = Field(default_factory=list)


class CommentTreeResponse(APIModel):
    answer_id: int
    total: int = Field(ge=0)
    items: list[CommentItem] = Field(default_factory=list)


CommentItem.model_rebuild()
