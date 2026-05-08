import oracledb

from app.core.errors import AppError, NotFoundError, ValidationError
from app.db.connection import get_connection
from app.repositories.answer_repository import AnswerRepository
from app.repositories.log_repository import LogRepository
from app.repositories.media_repository import MediaRepository
from app.repositories.question_repository import QuestionRepository
from app.schemas.answer import CreateManualAnswerRequest, DeleteAnswerResponse
from app.schemas.question import QuestionDetailResponse


class AnswerService:
    def __init__(
        self,
        answer_repository: AnswerRepository | None = None,
        question_repository: QuestionRepository | None = None,
        media_repository: MediaRepository | None = None,
        log_repository: LogRepository | None = None,
    ) -> None:
        self._answer_repository = answer_repository or AnswerRepository()
        self._question_repository = question_repository or QuestionRepository()
        self._media_repository = media_repository or MediaRepository()
        self._log_repository = log_repository or LogRepository()

    def create_manual_answer(
        self,
        *,
        question_id: int,
        payload: CreateManualAnswerRequest,
    ) -> QuestionDetailResponse:
        if question_id <= 0:
            raise ValidationError("question_id must be greater than 0.")

        with get_connection() as connection:
            question = self._question_repository.get_question_detail(connection, question_id)
            if question is None:
                raise NotFoundError(f"Question {question_id} was not found.")

            if question["status"] != "OPEN":
                raise ValidationError("Only OPEN questions can accept new answers.")

            try:
                self._answer_repository.create_manual_answer(
                    connection=connection,
                    question_id=question_id,
                    user_id=payload.user_id,
                    content=payload.content,
                    confidence_score=payload.confidence_score,
                )
                connection.commit()
            except oracledb.DatabaseError as exc:
                connection.rollback()
                raise self._translate_database_error(exc) from exc
            except Exception:
                connection.rollback()
                raise

            refreshed_question = self._question_repository.get_question_detail(
                connection,
                question_id,
            )
            if refreshed_question is None:
                raise NotFoundError("Answer was created but the question could not be reloaded.")

            refreshed_question["images"] = self._media_repository.list_active_media_by_owner(
                connection,
                owner_type="QUESTION",
                owner_id=question_id,
            )
            refreshed_question["answers"] = self._answer_repository.list_answers_by_question(
                connection,
                question_id,
            )
            self._attach_answer_images(connection, refreshed_question["answers"])

        return QuestionDetailResponse(**refreshed_question)

    def delete_answer(
        self,
        *,
        answer_id: int,
        current_user_id: int,
        current_user_role: str,
        reason: str | None = None,
    ) -> DeleteAnswerResponse:
        if answer_id <= 0:
            raise ValidationError("answer_id must be greater than 0.")
        if current_user_id <= 0:
            raise ValidationError("current_user_id must be greater than 0.")

        normalized_role = current_user_role.strip().upper()
        normalized_reason = self._normalize_reason(reason)

        with get_connection() as connection:
            answer = self._answer_repository.get_answer_delete_context(connection, answer_id)
            if answer is None:
                raise NotFoundError(f"Answer {answer_id} was not found.")
            if answer["status"] == "DELETED":
                raise ValidationError("Answer has already been deleted.")
            if answer["accepted_answer_id"] == answer_id:
                raise ValidationError(
                    "Accepted answers cannot be deleted before changing the accepted answer."
                )

            is_admin = normalized_role == "ADMIN"
            is_author = answer["user_id"] == current_user_id
            if not is_admin:
                if answer["answer_type"] != "MANUAL" or not is_author:
                    raise AppError("Only the answer author or an admin can delete this answer.", status_code=403)

            try:
                deleted_count = self._answer_repository.soft_delete_answer(
                    connection,
                    answer_id=answer_id,
                )
                if deleted_count == 0:
                    raise NotFoundError(f"Answer {answer_id} could not be deleted.")

                self._answer_repository.sync_question_answer_count(
                    connection,
                    question_id=answer["question_id"],
                )

                reason_part = f", reason={normalized_reason}" if normalized_reason else ""
                self._log_repository.create_operation_log(
                    connection,
                    user_id=current_user_id,
                    op_type="ADMIN_DELETE_ANSWER" if is_admin else "AUTHOR_DELETE_ANSWER",
                    op_content=(
                        f"answer_id={answer_id}, question_id={answer['question_id']}, "
                        f"question_title={answer['question_title']}, "
                        f"answer_type={answer['answer_type']}, from={answer['status']}, "
                        f"to=DELETED{reason_part}"
                    )[:500],
                )
                connection.commit()
            except oracledb.DatabaseError as exc:
                connection.rollback()
                raise self._translate_database_error(exc) from exc
            except Exception:
                connection.rollback()
                raise

        return DeleteAnswerResponse(
            answer_id=answer_id,
            question_id=answer["question_id"],
            status="DELETED",
            deleted=True,
            message="Answer deleted successfully.",
        )

    def _attach_answer_images(
        self,
        connection: oracledb.Connection,
        answers: list[dict],
    ) -> None:
        for answer in answers:
            answer["images"] = self._media_repository.list_active_media_by_owner(
                connection,
                owner_type="ANSWER",
                owner_id=answer["answer_id"],
            )

    @staticmethod
    def _translate_database_error(exc: oracledb.DatabaseError) -> AppError:
        details = exc.args[0] if exc.args else exc
        message = getattr(details, "message", str(details))

        if "ORA-02291" in message:
            return ValidationError("user_id or question_id contains an invalid reference.")
        if "ORA-02290" in message:
            return ValidationError("Manual answer data violates a database constraint.")

        return AppError(f"Database operation failed: {message}", status_code=500)

    @staticmethod
    def _normalize_reason(reason: str | None) -> str | None:
        if reason is None:
            return None
        normalized = " ".join(reason.strip().split())
        if len(normalized) > 200:
            raise ValidationError("reason must be at most 200 characters.")
        return normalized or None
