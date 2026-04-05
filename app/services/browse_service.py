import oracledb

from app.core.errors import AppError, NotFoundError, ValidationError
from app.db.connection import get_connection
from app.repositories.browse_repository import BrowseRepository
from app.schemas.browse import BrowseRecordResponse, CreateBrowseRecordRequest


class BrowseService:
    def __init__(
        self,
        browse_repository: BrowseRepository | None = None,
    ) -> None:
        self._browse_repository = browse_repository or BrowseRepository()

    def create_browse_record(
        self,
        *,
        question_id: int,
        payload: CreateBrowseRecordRequest,
    ) -> BrowseRecordResponse:
        if question_id <= 0:
            raise ValidationError("question_id must be greater than 0.")

        with get_connection() as connection:
            try:
                history_id = self._browse_repository.create_browse_record(
                    connection=connection,
                    question_id=question_id,
                    user_id=payload.user_id,
                    duration=payload.duration,
                    click_depth=payload.click_depth,
                )
                connection.commit()
            except oracledb.DatabaseError as exc:
                connection.rollback()
                raise self._translate_database_error(exc) from exc
            except Exception:
                connection.rollback()
                raise

            browse_record = self._browse_repository.get_browse_record(connection, history_id)
            if browse_record is None:
                raise NotFoundError("Browse record was created but could not be reloaded.")

            view_count = self._browse_repository.get_question_view_count(connection, question_id)
            if view_count is None:
                raise NotFoundError(
                    f"Question {question_id} was not found after recording browse history."
                )

        return BrowseRecordResponse(**browse_record, view_count=view_count)

    @staticmethod
    def _translate_database_error(exc: oracledb.DatabaseError) -> AppError:
        details = exc.args[0] if exc.args else exc
        message = getattr(details, "message", str(details))

        if "ORA-02291" in message:
            return ValidationError("user_id or question_id contains an invalid reference.")
        if "ORA-02290" in message:
            return ValidationError("duration or click_depth violates a database constraint.")

        return AppError(f"Database operation failed: {message}", status_code=500)
