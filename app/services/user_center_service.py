import re

from app.core.errors import NotFoundError, ValidationError
from app.db.connection import get_connection
from app.repositories.user_center_repository import UserCenterRepository
from app.schemas.user_center import (
    UpdateCurrentUserProfileRequest,
    UserAnswerListResponse,
    UserBrowseHistoryResponse,
    UserCenterProfileResponse,
    UserFavoriteListResponse,
    UserQuestionListResponse,
    UserSearchHistoryResponse,
)


class UserCenterService:
    _EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    _PHONE_PATTERN = re.compile(r"^[0-9+\-\s()]{6,20}$")

    def __init__(
        self,
        user_center_repository: UserCenterRepository | None = None,
    ) -> None:
        self._user_center_repository = user_center_repository or UserCenterRepository()

    def get_profile(
        self,
        *,
        user_id: int,
    ) -> UserCenterProfileResponse:
        self._validate_user_id(user_id)

        with get_connection() as connection:
            profile = self._user_center_repository.get_user_profile(connection, user_id)
            if profile is None:
                raise NotFoundError(f"User {user_id} was not found.")

        return UserCenterProfileResponse(**profile)

    def update_current_profile(
        self,
        *,
        user_id: int,
        payload: UpdateCurrentUserProfileRequest,
    ) -> UserCenterProfileResponse:
        self._validate_user_id(user_id)

        updates = payload.model_dump(exclude_unset=True)
        if not updates:
            raise ValidationError("At least one profile field must be provided.")

        with get_connection() as connection:
            current_profile = self._user_center_repository.get_user_profile(connection, user_id)
            if current_profile is None:
                raise NotFoundError(f"User {user_id} was not found.")

            nickname = self._normalize_nickname(
                updates["nickname"] if "nickname" in updates else current_profile.get("nickname")
            )
            email = self._normalize_email(
                updates["email"] if "email" in updates else current_profile.get("email")
            )
            phone = self._normalize_phone(
                updates["phone"] if "phone" in updates else current_profile.get("phone")
            )

            if email is not None and self._user_center_repository.email_exists_for_other_user(
                connection,
                email=email,
                user_id=user_id,
            ):
                raise ValidationError("该邮箱已被其他账号使用。")

            if phone is not None and self._user_center_repository.phone_exists_for_other_user(
                connection,
                phone=phone,
                user_id=user_id,
            ):
                raise ValidationError("该手机号已被其他账号使用。")

            updated_count = self._user_center_repository.update_user_profile(
                connection,
                user_id=user_id,
                nickname=nickname,
                email=email,
                phone=phone,
            )
            if updated_count <= 0:
                raise NotFoundError(f"User {user_id} was not found.")

            connection.commit()
            profile = self._user_center_repository.get_user_profile(connection, user_id)
            assert profile is not None

        return UserCenterProfileResponse(**profile)

    def list_questions(
        self,
        *,
        user_id: int,
        page: int = 1,
        page_size: int = 10,
    ) -> UserQuestionListResponse:
        self._validate_user_id(user_id)
        self._validate_page(page=page, page_size=page_size)

        with get_connection() as connection:
            self._ensure_user_exists(connection, user_id)
            items = self._user_center_repository.list_user_questions(
                connection,
                user_id=user_id,
                page=page,
                page_size=page_size,
            )
            total = self._user_center_repository.count_user_questions(
                connection,
                user_id=user_id,
            )

        return UserQuestionListResponse(
            user_id=user_id,
            page=page,
            page_size=page_size,
            total=total,
            items=items,
        )

    def list_answers(
        self,
        *,
        user_id: int,
        page: int = 1,
        page_size: int = 10,
    ) -> UserAnswerListResponse:
        self._validate_user_id(user_id)
        self._validate_page(page=page, page_size=page_size)

        with get_connection() as connection:
            self._ensure_user_exists(connection, user_id)
            items = self._user_center_repository.list_user_answers(
                connection,
                user_id=user_id,
                page=page,
                page_size=page_size,
            )
            total = self._user_center_repository.count_user_answers(
                connection,
                user_id=user_id,
            )

        return UserAnswerListResponse(
            user_id=user_id,
            page=page,
            page_size=page_size,
            total=total,
            items=items,
        )

    def list_favorites(
        self,
        *,
        user_id: int,
        page: int = 1,
        page_size: int = 10,
    ) -> UserFavoriteListResponse:
        self._validate_user_id(user_id)
        self._validate_page(page=page, page_size=page_size)

        with get_connection() as connection:
            self._ensure_user_exists(connection, user_id)
            items = self._user_center_repository.list_user_favorites(
                connection,
                user_id=user_id,
                page=page,
                page_size=page_size,
            )
            total = self._user_center_repository.count_user_favorites(
                connection,
                user_id=user_id,
            )

        return UserFavoriteListResponse(
            user_id=user_id,
            page=page,
            page_size=page_size,
            total=total,
            items=items,
        )

    def list_browse_history(
        self,
        *,
        user_id: int,
        limit: int = 10,
    ) -> UserBrowseHistoryResponse:
        self._validate_user_id(user_id)
        self._validate_limit(limit)

        with get_connection() as connection:
            self._ensure_user_exists(connection, user_id)
            items = self._user_center_repository.list_user_browse_history(
                connection,
                user_id=user_id,
                limit=limit,
            )

        return UserBrowseHistoryResponse(
            user_id=user_id,
            limit=limit,
            item_count=len(items),
            items=items,
        )

    def list_search_history(
        self,
        *,
        user_id: int,
        limit: int = 10,
    ) -> UserSearchHistoryResponse:
        self._validate_user_id(user_id)
        self._validate_limit(limit)

        with get_connection() as connection:
            self._ensure_user_exists(connection, user_id)
            items = self._user_center_repository.list_user_search_history(
                connection,
                user_id=user_id,
                limit=limit,
            )

        return UserSearchHistoryResponse(
            user_id=user_id,
            limit=limit,
            item_count=len(items),
            items=items,
        )

    def _ensure_user_exists(self, connection, user_id: int) -> None:
        if not self._user_center_repository.user_exists(connection, user_id):
            raise NotFoundError(f"User {user_id} was not found.")

    @staticmethod
    def _validate_user_id(user_id: int) -> None:
        if user_id <= 0:
            raise ValidationError("user_id must be greater than 0.")

    @staticmethod
    def _validate_page(*, page: int, page_size: int) -> None:
        if page <= 0:
            raise ValidationError("page must be greater than 0.")
        if page_size <= 0 or page_size > 50:
            raise ValidationError("page_size must be between 1 and 50.")

    @staticmethod
    def _validate_limit(limit: int) -> None:
        if limit <= 0 or limit > 50:
            raise ValidationError("limit must be between 1 and 50.")

    def _normalize_nickname(self, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        if not normalized:
            return None
        if len(normalized) > 50:
            raise ValidationError("nickname must be 50 characters or fewer.")
        return normalized

    def _normalize_email(self, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        if not normalized:
            return None
        if len(normalized) > 100:
            raise ValidationError("email must be 100 characters or fewer.")
        if not self._EMAIL_PATTERN.fullmatch(normalized):
            raise ValidationError("email format is invalid.")
        return normalized

    def _normalize_phone(self, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        if not normalized:
            return None
        if len(normalized) > 20:
            raise ValidationError("phone must be 20 characters or fewer.")
        if not self._PHONE_PATTERN.fullmatch(normalized):
            raise ValidationError("phone format is invalid.")
        return normalized
