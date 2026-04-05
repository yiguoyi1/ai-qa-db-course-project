from app.db.connection import get_connection
from app.repositories.meta_repository import MetaRepository
from app.schemas.meta import CategoryListResponse, TagListResponse


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

    def list_tags(self) -> TagListResponse:
        with get_connection() as connection:
            items = self._meta_repository.list_tags(connection)

        return TagListResponse(items=items)
