import oracledb

from app.core.errors import AppError, NotFoundError, ValidationError
from app.db.connection import get_connection
from app.repositories.recommendation_repository import RecommendationRepository
from app.schemas.recommendation import (
    ProfileRebuildResponse,
    RecommendationGenerationResponse,
    RecommendationListResponse,
)


class RecommendationService:
    VALID_RECOMMENDATION_STATUSES = {"ACTIVE", "EXPIRED", "DISMISSED"}

    def __init__(
        self,
        recommendation_repository: RecommendationRepository | None = None,
    ) -> None:
        self._recommendation_repository = (
            recommendation_repository or RecommendationRepository()
        )

    def rebuild_profile(
        self,
        *,
        user_id: int,
    ) -> ProfileRebuildResponse:
        self._validate_user_id(user_id)

        with get_connection() as connection:
            self._ensure_user_exists(connection, user_id)
            try:
                self._recommendation_repository.rebuild_user_tag_profile(connection, user_id)
                connection.commit()
            except oracledb.DatabaseError as exc:
                connection.rollback()
                raise self._translate_database_error(exc) from exc
            except Exception:
                connection.rollback()
                raise

            items = self._recommendation_repository.list_user_tag_profile(connection, user_id)

        return ProfileRebuildResponse(
            user_id=user_id,
            item_count=len(items),
            items=items,
        )

    def generate_recommendations(
        self,
        *,
        user_id: int,
        limit: int = 10,
    ) -> RecommendationGenerationResponse:
        self._validate_user_id(user_id)
        if limit <= 0 or limit > 50:
            raise ValidationError("limit must be between 1 and 50.")

        with get_connection() as connection:
            self._ensure_user_exists(connection, user_id)
            try:
                self._recommendation_repository.generate_recommendations(
                    connection,
                    user_id,
                    limit,
                )
                connection.commit()
            except oracledb.DatabaseError as exc:
                connection.rollback()
                raise self._translate_database_error(exc) from exc
            except Exception:
                connection.rollback()
                raise

            active_count = self._recommendation_repository.count_recommendations(
                connection,
                user_id=user_id,
                status="ACTIVE",
            )

        return RecommendationGenerationResponse(
            user_id=user_id,
            requested_limit=limit,
            active_count=active_count,
        )

    def list_recommendations(
        self,
        *,
        user_id: int,
        status: str = "ACTIVE",
        limit: int | None = None,
    ) -> RecommendationListResponse:
        self._validate_user_id(user_id)
        if limit is not None and (limit <= 0 or limit > 100):
            raise ValidationError("limit must be between 1 and 100.")

        normalized_status = status.strip().upper()
        if normalized_status not in self.VALID_RECOMMENDATION_STATUSES:
            raise ValidationError("status must be one of ACTIVE, EXPIRED, or DISMISSED.")

        with get_connection() as connection:
            self._ensure_user_exists(connection, user_id)
            items = self._recommendation_repository.list_recommendations(
                connection,
                user_id=user_id,
                status=normalized_status,
                limit=limit,
            )

        return RecommendationListResponse(
            user_id=user_id,
            status=normalized_status,
            total=len(items),
            items=items,
        )

    def _ensure_user_exists(
        self,
        connection: oracledb.Connection,
        user_id: int,
    ) -> None:
        if not self._recommendation_repository.user_exists(connection, user_id):
            raise NotFoundError(f"User {user_id} was not found.")

    @staticmethod
    def _validate_user_id(user_id: int) -> None:
        if user_id <= 0:
            raise ValidationError("user_id must be greater than 0.")

    @staticmethod
    def _translate_database_error(exc: oracledb.DatabaseError) -> AppError:
        details = exc.args[0] if exc.args else exc
        message = getattr(details, "message", str(details))
        return AppError(f"Database operation failed: {message}", status_code=500)
