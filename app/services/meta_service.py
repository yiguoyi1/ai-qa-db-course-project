import re

from app.core.errors import ValidationError
from app.db.connection import get_connection
from app.repositories.meta_repository import MetaRepository
from app.schemas.meta import CategoryListResponse, TagListResponse, TagSuggestionResponse


class MetaService:
    def __init__(
        self,
        meta_repository: MetaRepository | None = None,
    ) -> None:
        self._meta_repository = meta_repository or MetaRepository()

    def list_categories(self) -> CategoryListResponse:
        with get_connection() as connection:
            items = self._meta_repository.list_categories(connection)

        return CategoryListResponse(items=items)

    def list_tags(self, *, limit: int | None = None) -> TagListResponse:
        if limit is not None and (limit <= 0 or limit > 200):
            raise ValidationError("limit must be between 1 and 200.")

        with get_connection() as connection:
            items = self._meta_repository.list_tags(connection, limit=limit)

        return TagListResponse(items=items)

    def suggest_tags(
        self,
        *,
        keyword: str | None = None,
        limit: int = 10,
    ) -> TagSuggestionResponse:
        if limit <= 0 or limit > 20:
            raise ValidationError("limit must be between 1 and 20.")

        normalized_keyword = self._normalize_keyword(keyword)

        with get_connection() as connection:
            items = self._meta_repository.suggest_tags(
                connection,
                keyword=normalized_keyword,
                limit=limit,
            )

        return TagSuggestionResponse(items=items)

    @staticmethod
    def _normalize_keyword(value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip().lstrip("#").lower()
        normalized = re.sub(r"\s+", "-", normalized)
        return normalized or None
