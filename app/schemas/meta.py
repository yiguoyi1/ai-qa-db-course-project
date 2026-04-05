from pydantic import BaseModel, Field


class CategoryItem(BaseModel):
    category_id: int
    category_name: str
    description: str | None = None
    status: str


class CategoryListResponse(BaseModel):
    items: list[CategoryItem] = Field(default_factory=list)


class TagOptionItem(BaseModel):
    tag_id: int
    tag_name: str


class TagListResponse(BaseModel):
    items: list[TagOptionItem] = Field(default_factory=list)
