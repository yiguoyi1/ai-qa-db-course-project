from pathlib import Path

import oracledb

from app.core.errors import AppError, NotFoundError, ValidationError
from app.core.file_storage import (
    delete_stored_file,
    save_answer_image_bytes,
    save_avatar_bytes,
    save_question_image_bytes,
)
from app.db.connection import get_connection
from app.repositories.answer_repository import AnswerRepository
from app.repositories.media_repository import MediaRepository
from app.repositories.question_repository import QuestionRepository
from app.schemas.media import (
    AnswerImageDeleteResponse,
    AnswerImageListResponse,
    AvatarDeleteResponse,
    AvatarMediaResponse,
    MediaAssetItem,
    QuestionImageDeleteResponse,
    QuestionImageListResponse,
)


class MediaService:
    ALLOWED_IMAGE_MIME_TYPES = {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp",
    }
    MAX_AVATAR_SIZE = 2 * 1024 * 1024
    MAX_QUESTION_IMAGE_SIZE = 5 * 1024 * 1024
    MAX_QUESTION_IMAGE_COUNT = 9
    MAX_ANSWER_IMAGE_SIZE = 5 * 1024 * 1024
    MAX_ANSWER_IMAGE_COUNT = 6

    def __init__(
        self,
        media_repository: MediaRepository | None = None,
        question_repository: QuestionRepository | None = None,
        answer_repository: AnswerRepository | None = None,
    ) -> None:
        self._media_repository = media_repository or MediaRepository()
        self._question_repository = question_repository or QuestionRepository()
        self._answer_repository = answer_repository or AnswerRepository()

    def get_current_user_avatar(self, *, user_id: int) -> AvatarMediaResponse:
        with get_connection() as connection:
            avatar = self._media_repository.get_active_avatar_by_user_id(connection, user_id)
            if avatar is None:
                raise NotFoundError("Avatar was not found.")

        return self._to_avatar_response(avatar)

    def upload_current_user_avatar(
        self,
        *,
        user_id: int,
        original_file_name: str | None,
        mime_type: str | None,
        content: bytes,
    ) -> AvatarMediaResponse:
        normalized_mime_type = self._normalize_image_mime_type(mime_type)
        self._validate_bytes(content, max_size=self.MAX_AVATAR_SIZE, label="Avatar")
        file_ext = self._resolve_file_ext(
            original_file_name=original_file_name,
            mime_type=normalized_mime_type,
        )

        stored_file = save_avatar_bytes(content=content, file_ext=file_ext)
        previous_avatar = None

        with get_connection() as connection:
            try:
                previous_avatar = self._media_repository.get_active_avatar_by_user_id(connection, user_id)

                media_id = self._media_repository.create_media_asset(
                    connection,
                    uploader_user_id=user_id,
                    owner_type="USER_AVATAR",
                    owner_id=user_id,
                    file_name=stored_file.file_name,
                    original_file_name=original_file_name,
                    mime_type=normalized_mime_type,
                    file_ext=file_ext.lstrip("."),
                    file_size=len(content),
                    storage_path=stored_file.storage_path,
                    public_url=stored_file.public_url,
                )

                updated_count = self._media_repository.update_user_avatar_media(
                    connection,
                    user_id=user_id,
                    media_id=media_id,
                )
                if updated_count == 0:
                    raise NotFoundError(f"User {user_id} was not found.")

                if previous_avatar is not None:
                    self._media_repository.mark_media_deleted(
                        connection,
                        media_id=previous_avatar["media_id"],
                    )

                connection.commit()
                avatar = self._media_repository.get_active_avatar_by_user_id(connection, user_id)
                assert avatar is not None
            except oracledb.DatabaseError as exc:
                connection.rollback()
                delete_stored_file(stored_file.storage_path)
                raise self._translate_database_error(exc) from exc
            except Exception:
                connection.rollback()
                delete_stored_file(stored_file.storage_path)
                raise

        if previous_avatar is not None:
            delete_stored_file(previous_avatar.get("storage_path"))

        return self._to_avatar_response(avatar)

    def delete_current_user_avatar(self, *, user_id: int) -> AvatarDeleteResponse:
        with get_connection() as connection:
            avatar = self._media_repository.get_active_avatar_by_user_id(connection, user_id)
            if avatar is None:
                raise NotFoundError("Avatar was not found.")

            try:
                self._media_repository.update_user_avatar_media(
                    connection,
                    user_id=user_id,
                    media_id=None,
                )
                self._media_repository.mark_media_deleted(
                    connection,
                    media_id=avatar["media_id"],
                )
                connection.commit()
            except oracledb.DatabaseError as exc:
                connection.rollback()
                raise self._translate_database_error(exc) from exc
            except Exception:
                connection.rollback()
                raise

        delete_stored_file(avatar.get("storage_path"))
        return AvatarDeleteResponse(message="Avatar deleted successfully.")

    def upload_question_image(
        self,
        *,
        user_id: int,
        question_id: int,
        original_file_name: str | None,
        mime_type: str | None,
        content: bytes,
    ) -> QuestionImageListResponse:
        normalized_mime_type = self._normalize_image_mime_type(mime_type)
        self._validate_bytes(content, max_size=self.MAX_QUESTION_IMAGE_SIZE, label="Question image")
        file_ext = self._resolve_file_ext(
            original_file_name=original_file_name,
            mime_type=normalized_mime_type,
        )

        stored_file = save_question_image_bytes(content=content, file_ext=file_ext)

        with get_connection() as connection:
            try:
                self._ensure_question_author(connection, question_id=question_id, user_id=user_id)
                current_count = self._media_repository.count_active_media_by_owner(
                    connection,
                    owner_type="QUESTION",
                    owner_id=question_id,
                )
                if current_count >= self.MAX_QUESTION_IMAGE_COUNT:
                    raise ValidationError("A question can have at most 9 active images.")

                sort_order = self._media_repository.get_next_sort_order_for_owner(
                    connection,
                    owner_type="QUESTION",
                    owner_id=question_id,
                )

                self._media_repository.create_media_asset(
                    connection,
                    uploader_user_id=user_id,
                    owner_type="QUESTION",
                    owner_id=question_id,
                    file_name=stored_file.file_name,
                    original_file_name=original_file_name,
                    mime_type=normalized_mime_type,
                    file_ext=file_ext.lstrip("."),
                    file_size=len(content),
                    storage_path=stored_file.storage_path,
                    public_url=stored_file.public_url,
                    sort_order=sort_order,
                )
                connection.commit()
                items = self._media_repository.list_active_media_by_owner(
                    connection,
                    owner_type="QUESTION",
                    owner_id=question_id,
                )
            except oracledb.DatabaseError as exc:
                connection.rollback()
                delete_stored_file(stored_file.storage_path)
                raise self._translate_database_error(exc) from exc
            except Exception:
                connection.rollback()
                delete_stored_file(stored_file.storage_path)
                raise

        return QuestionImageListResponse(
            question_id=question_id,
            items=[self._to_media_item(item) for item in items],
            total=len(items),
        )

    def delete_question_image(
        self,
        *,
        user_id: int,
        question_id: int,
        media_id: int,
    ) -> QuestionImageDeleteResponse:
        with get_connection() as connection:
            self._ensure_question_author(connection, question_id=question_id, user_id=user_id)
            media = self._media_repository.get_active_media_by_id(
                connection,
                media_id=media_id,
                owner_type="QUESTION",
                owner_id=question_id,
            )
            if media is None:
                raise NotFoundError(f"Question image {media_id} was not found.")

            try:
                self._media_repository.mark_media_deleted(connection, media_id=media_id)
                connection.commit()
            except oracledb.DatabaseError as exc:
                connection.rollback()
                raise self._translate_database_error(exc) from exc
            except Exception:
                connection.rollback()
                raise

        delete_stored_file(media.get("storage_path"))
        return QuestionImageDeleteResponse(
            question_id=question_id,
            media_id=media_id,
            message="Question image deleted successfully.",
        )

    def list_question_images(self, *, question_id: int) -> QuestionImageListResponse:
        with get_connection() as connection:
            question = self._question_repository.get_question_detail(connection, question_id)
            if question is None:
                raise NotFoundError(f"Question {question_id} was not found.")
            items = self._media_repository.list_active_media_by_owner(
                connection,
                owner_type="QUESTION",
                owner_id=question_id,
            )

        return QuestionImageListResponse(
            question_id=question_id,
            items=[self._to_media_item(item) for item in items],
            total=len(items),
        )

    def list_question_image_items(
        self,
        connection: oracledb.Connection,
        *,
        question_id: int,
    ) -> list[MediaAssetItem]:
        items = self._media_repository.list_active_media_by_owner(
            connection,
            owner_type="QUESTION",
            owner_id=question_id,
        )
        return [self._to_media_item(item) for item in items]

    def upload_answer_image(
        self,
        *,
        user_id: int,
        answer_id: int,
        original_file_name: str | None,
        mime_type: str | None,
        content: bytes,
    ) -> AnswerImageListResponse:
        normalized_mime_type = self._normalize_image_mime_type(mime_type)
        self._validate_bytes(content, max_size=self.MAX_ANSWER_IMAGE_SIZE, label="Answer image")
        file_ext = self._resolve_file_ext(
            original_file_name=original_file_name,
            mime_type=normalized_mime_type,
        )

        stored_file = save_answer_image_bytes(content=content, file_ext=file_ext)

        with get_connection() as connection:
            try:
                self._ensure_answer_author(connection, answer_id=answer_id, user_id=user_id)
                current_count = self._media_repository.count_active_media_by_owner(
                    connection,
                    owner_type="ANSWER",
                    owner_id=answer_id,
                )
                if current_count >= self.MAX_ANSWER_IMAGE_COUNT:
                    raise ValidationError("An answer can have at most 6 active images.")

                sort_order = self._media_repository.get_next_sort_order_for_owner(
                    connection,
                    owner_type="ANSWER",
                    owner_id=answer_id,
                )

                self._media_repository.create_media_asset(
                    connection,
                    uploader_user_id=user_id,
                    owner_type="ANSWER",
                    owner_id=answer_id,
                    file_name=stored_file.file_name,
                    original_file_name=original_file_name,
                    mime_type=normalized_mime_type,
                    file_ext=file_ext.lstrip("."),
                    file_size=len(content),
                    storage_path=stored_file.storage_path,
                    public_url=stored_file.public_url,
                    sort_order=sort_order,
                )
                connection.commit()
                items = self._media_repository.list_active_media_by_owner(
                    connection,
                    owner_type="ANSWER",
                    owner_id=answer_id,
                )
            except oracledb.DatabaseError as exc:
                connection.rollback()
                delete_stored_file(stored_file.storage_path)
                raise self._translate_database_error(exc) from exc
            except Exception:
                connection.rollback()
                delete_stored_file(stored_file.storage_path)
                raise

        return AnswerImageListResponse(
            answer_id=answer_id,
            items=[self._to_media_item(item) for item in items],
            total=len(items),
        )

    def delete_answer_image(
        self,
        *,
        user_id: int,
        answer_id: int,
        media_id: int,
    ) -> AnswerImageDeleteResponse:
        with get_connection() as connection:
            self._ensure_answer_author(connection, answer_id=answer_id, user_id=user_id)
            media = self._media_repository.get_active_media_by_id(
                connection,
                media_id=media_id,
                owner_type="ANSWER",
                owner_id=answer_id,
            )
            if media is None:
                raise NotFoundError(f"Answer image {media_id} was not found.")

            try:
                self._media_repository.mark_media_deleted(connection, media_id=media_id)
                connection.commit()
            except oracledb.DatabaseError as exc:
                connection.rollback()
                raise self._translate_database_error(exc) from exc
            except Exception:
                connection.rollback()
                raise

        delete_stored_file(media.get("storage_path"))
        return AnswerImageDeleteResponse(
            answer_id=answer_id,
            media_id=media_id,
            message="Answer image deleted successfully.",
        )

    def list_answer_images(self, *, answer_id: int) -> AnswerImageListResponse:
        with get_connection() as connection:
            answer = self._answer_repository.get_answer_by_id(connection, answer_id)
            if answer is None:
                raise NotFoundError(f"Answer {answer_id} was not found.")
            items = self._media_repository.list_active_media_by_owner(
                connection,
                owner_type="ANSWER",
                owner_id=answer_id,
            )

        return AnswerImageListResponse(
            answer_id=answer_id,
            items=[self._to_media_item(item) for item in items],
            total=len(items),
        )

    def list_answer_image_items(
        self,
        connection: oracledb.Connection,
        *,
        answer_id: int,
    ) -> list[MediaAssetItem]:
        items = self._media_repository.list_active_media_by_owner(
            connection,
            owner_type="ANSWER",
            owner_id=answer_id,
        )
        return [self._to_media_item(item) for item in items]

    def _ensure_question_author(
        self,
        connection: oracledb.Connection,
        *,
        question_id: int,
        user_id: int,
    ) -> None:
        question = self._question_repository.get_question_detail(connection, question_id)
        if question is None:
            raise NotFoundError(f"Question {question_id} was not found.")
        if question["user_id"] != user_id:
            raise AppError(
                "Only the question author can manage images for this question.",
                status_code=403,
            )

    def _ensure_answer_author(
        self,
        connection: oracledb.Connection,
        *,
        answer_id: int,
        user_id: int,
    ) -> None:
        answer = self._answer_repository.get_answer_by_id(connection, answer_id)
        if answer is None:
            raise NotFoundError(f"Answer {answer_id} was not found.")
        if answer["answer_type"] != "MANUAL" or answer["user_id"] is None:
            raise AppError(
                "Only manual answer authors can manage images for this answer.",
                status_code=403,
            )
        if answer["user_id"] != user_id:
            raise AppError(
                "Only the answer author can manage images for this answer.",
                status_code=403,
            )

    def _normalize_image_mime_type(self, mime_type: str | None) -> str:
        normalized = (mime_type or "").strip().lower()
        if normalized not in self.ALLOWED_IMAGE_MIME_TYPES:
            raise ValidationError(
                "Image MIME type must be image/jpeg, image/png, or image/webp."
            )
        return normalized

    @staticmethod
    def _validate_bytes(content: bytes, *, max_size: int, label: str) -> None:
        if not content:
            raise ValidationError(f"{label} file must not be empty.")
        if len(content) > max_size:
            limit_mb = max_size // (1024 * 1024)
            raise ValidationError(f"{label} file size must be at most {limit_mb}MB.")

    def _resolve_file_ext(
        self,
        *,
        original_file_name: str | None,
        mime_type: str,
    ) -> str:
        fallback_ext = self.ALLOWED_IMAGE_MIME_TYPES[mime_type]
        if not original_file_name:
            return fallback_ext

        suffix = Path(original_file_name).suffix.lower()
        if suffix in {".jpg", ".jpeg", ".png", ".webp"}:
            if mime_type == "image/jpeg":
                return ".jpg"
            return suffix

        return fallback_ext

    @staticmethod
    def _to_avatar_response(item: dict) -> AvatarMediaResponse:
        return AvatarMediaResponse(
            media_id=item["media_id"],
            owner_type=item["owner_type"],
            owner_id=item["owner_id"],
            public_url=item["public_url"],
            mime_type=item["mime_type"],
            file_size=item["file_size"],
            status=item["status"],
            create_time=item["create_time"],
            update_time=item["update_time"],
        )

    @staticmethod
    def _to_media_item(item: dict) -> MediaAssetItem:
        return MediaAssetItem(
            media_id=item["media_id"],
            owner_type=item["owner_type"],
            owner_id=item["owner_id"],
            public_url=item["public_url"],
            mime_type=item["mime_type"],
            file_size=item["file_size"],
            sort_order=item["sort_order"],
            status=item["status"],
            create_time=item["create_time"],
            update_time=item["update_time"],
        )

    @staticmethod
    def _translate_database_error(exc: oracledb.DatabaseError) -> AppError:
        details = exc.args[0] if exc.args else exc
        message = getattr(details, "message", str(details))

        if "ORA-02291" in message:
            return ValidationError("Media owner references an invalid user, question, or answer.")
        if "ORA-02290" in message:
            return ValidationError("Media data violates a database constraint.")

        return AppError(f"Database operation failed: {message}", status_code=500)
