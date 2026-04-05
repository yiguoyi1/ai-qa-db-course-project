import oracledb

from app.core.errors import AppError, NotFoundError, ValidationError
from app.db.connection import get_connection
from app.repositories.favorite_repository import FavoriteRepository
from app.schemas.favorite import (
    CreateFavoriteRequest,
    FavoriteDeleteResponse,
    FavoriteRecordResponse,
)


class FavoriteService:
    def __init__(
        self,
        favorite_repository: FavoriteRepository | None = None,
    ) -> None:
        self._favorite_repository = favorite_repository or FavoriteRepository()

    def create_favorite(
        self,
        *,
        question_id: int,
        payload: CreateFavoriteRequest,
    ) -> FavoriteRecordResponse:
        if question_id <= 0:
            raise ValidationError("question_id must be greater than 0.")

        with get_connection() as connection:
            try:
                favorite_id = self._favorite_repository.create_favorite(
                    connection=connection,
                    question_id=question_id,
                    user_id=payload.user_id,
                )
                connection.commit()
            except oracledb.DatabaseError as exc:
                connection.rollback()
                raise self._translate_database_error(exc) from exc
            except Exception:
                connection.rollback()
                raise

            favorite_record = self._favorite_repository.get_favorite_record(
                connection,
                favorite_id,
            )
            if favorite_record is None:
                raise NotFoundError("Favorite was created but could not be reloaded.")

            favorite_count = self._favorite_repository.get_question_favorite_count(
                connection,
                question_id,
            )
            if favorite_count is None:
                raise NotFoundError(
                    f"Question {question_id} was not found after creating the favorite."
                )

        return FavoriteRecordResponse(**favorite_record, favorite_count=favorite_count)

    def delete_favorite(
        self,
        *,
        question_id: int,
        user_id: int,
    ) -> FavoriteDeleteResponse:
        if question_id <= 0:
            raise ValidationError("question_id must be greater than 0.")
        if user_id <= 0:
            raise ValidationError("user_id must be greater than 0.")

        with get_connection() as connection:
            try:
                deleted_count = self._favorite_repository.delete_favorite(
                    connection=connection,
                    question_id=question_id,
                    user_id=user_id,
                )
                connection.commit()
            except oracledb.DatabaseError as exc:
                connection.rollback()
                raise self._translate_database_error(exc) from exc
            except Exception:
                connection.rollback()
                raise

            favorite_count = self._favorite_repository.get_question_favorite_count(
                connection,
                question_id,
            )
            if favorite_count is None:
                raise NotFoundError(f"Question {question_id} was not found.")
            if deleted_count == 0:
                raise NotFoundError(
                    f"Favorite for question {question_id} and user {user_id} was not found."
                )

        return FavoriteDeleteResponse(
            question_id=question_id,
            user_id=user_id,
            favorite_count=favorite_count,
            deleted=True,
        )

    @staticmethod
    def _translate_database_error(exc: oracledb.DatabaseError) -> AppError:
        details = exc.args[0] if exc.args else exc
        message = getattr(details, "message", str(details))

        if "ORA-02291" in message:
            return ValidationError("user_id or question_id contains an invalid reference.")
        if "ORA-00001" in message:
            return ValidationError("This user has already favorited the question.")

        return AppError(f"Database operation failed: {message}", status_code=500)
