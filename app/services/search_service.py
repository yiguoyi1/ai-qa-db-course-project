import oracledb

from app.core.errors import AppError, ValidationError
from app.core.settings import get_settings
from app.db.connection import get_connection
from app.repositories.search_repository import SearchRepository
from app.schemas.question import QuestionListResponse


class SearchService:
    VALID_QUESTION_STATUSES = {"OPEN", "RESOLVED", "CLOSED", "ARCHIVED"}

    def __init__(
        self,
        search_repository: SearchRepository | None = None,
    ) -> None:
        self._search_repository = search_repository or SearchRepository()

    def search_questions(
        self,
        *,
        q: str,
        page: int = 1,
        page_size: int = 10,
        user_id: int | None = None,
        category_id: int | None = None,
        tag_id: int | None = None,
        status: str | None = None,
    ) -> QuestionListResponse:
        keyword = q.strip()
        if not keyword:
            raise ValidationError("q must not be empty.")
        if len(keyword) > 100:
            raise ValidationError("q must not be longer than 100 characters.")
        if page <= 0:
            raise ValidationError("page must be greater than 0.")
        if page_size <= 0 or page_size > 50:
            raise ValidationError("page_size must be between 1 and 50.")
        if user_id is not None and user_id <= 0:
            raise ValidationError("user_id must be greater than 0.")
        if category_id is not None and category_id <= 0:
            raise ValidationError("category_id must be greater than 0.")
        if tag_id is not None and tag_id <= 0:
            raise ValidationError("tag_id must be greater than 0.")

        normalized_status = status.strip().upper() if status is not None else None
        if normalized_status == "":
            normalized_status = None

        if (
            normalized_status is not None
            and normalized_status not in self.VALID_QUESTION_STATUSES
        ):
            raise ValidationError(
                "status must be one of OPEN, RESOLVED, CLOSED, or ARCHIVED."
            )

        use_oracle_text = get_settings().search_use_oracle_text

        with get_connection() as connection:
            try:
                items = self._search_repository.search_questions(
                    connection=connection,
                    keyword=keyword,
                    page=page,
                    page_size=page_size,
                    current_user_id=user_id,
                    category_id=category_id,
                    tag_id=tag_id,
                    status=normalized_status,
                    use_oracle_text=use_oracle_text,
                )
                total = self._search_repository.count_search_results(
                    connection=connection,
                    keyword=keyword,
                    category_id=category_id,
                    tag_id=tag_id,
                    status=normalized_status,
                    use_oracle_text=use_oracle_text,
                )
            except oracledb.DatabaseError as exc:
                if not (use_oracle_text and self._is_oracle_text_unavailable(exc)):
                    connection.rollback()
                    raise self._translate_database_error(exc) from exc

                connection.rollback()
                try:
                    items = self._search_repository.search_questions(
                        connection=connection,
                        keyword=keyword,
                        page=page,
                        page_size=page_size,
                        current_user_id=user_id,
                        category_id=category_id,
                        tag_id=tag_id,
                        status=normalized_status,
                        use_oracle_text=False,
                    )
                    total = self._search_repository.count_search_results(
                        connection=connection,
                        keyword=keyword,
                        category_id=category_id,
                        tag_id=tag_id,
                        status=normalized_status,
                        use_oracle_text=False,
                    )
                except oracledb.DatabaseError as fallback_exc:
                    connection.rollback()
                    raise self._translate_database_error(fallback_exc) from fallback_exc

            try:
                if user_id is not None:
                    self._search_repository.create_search_history(
                        connection=connection,
                        user_id=user_id,
                        keyword=keyword,
                    )
                    connection.commit()
            except oracledb.DatabaseError as exc:
                connection.rollback()
                raise self._translate_database_error(exc) from exc
            except Exception:
                connection.rollback()
                raise

        return QuestionListResponse(
            items=items,
            page=page,
            page_size=page_size,
            total=total,
        )

    @staticmethod
    def _translate_database_error(exc: oracledb.DatabaseError) -> AppError:
        details = exc.args[0] if exc.args else exc
        message = getattr(details, "message", str(details))

        if "ORA-02291" in message:
            return ValidationError("user_id contains an invalid reference.")

        return AppError(f"Database operation failed: {message}", status_code=500)

    @staticmethod
    def _is_oracle_text_unavailable(exc: oracledb.DatabaseError) -> bool:
        details = exc.args[0] if exc.args else exc
        message = getattr(details, "message", str(details))
        return any(token in message for token in ("DRG-", "ORA-29855", "ORA-20000"))

    # 🌟 新增：向库管员要历史记录
    def get_search_history(self, user_id: int) -> list[str]:
        with get_connection() as connection:
            return self._search_repository.get_search_history(connection, user_id)
