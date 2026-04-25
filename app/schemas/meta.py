from pydantic import Field

from app.schemas.base import APIModel


class CategoryItem(APIModel):
    category_id: int
    category_name: str
    description: str | None = None
    status: str


class CategoryListResponse(APIModel):
    items: list[CategoryItem] = Field(default_factory=list)


class TagOptionItem(APIModel):
    tag_id: int
    tag_name: str


class TagListResponse(APIModel):
    items: list[TagOptionItem] = Field(default_factory=list)
