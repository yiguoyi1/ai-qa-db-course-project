import oracledb

from app.core.errors import AppError, NotFoundError, ValidationError
from app.db.connection import get_connection
from app.repositories.feedback_repository import FeedbackRepository
from app.schemas.feedback import AnswerFeedbackResponse, SaveAnswerFeedbackRequest


class FeedbackService:
    def __init__(
        self,
        feedback_repository: FeedbackRepository | None = None,
    ) -> None:
        self._feedback_repository = feedback_repository or FeedbackRepository()

    def save_feedback(
        self,
        *,
        answer_id: int,
        payload: SaveAnswerFeedbackRequest,
    ) -> AnswerFeedbackResponse:
        if answer_id <= 0:
            raise ValidationError("answer_id must be greater than 0.")

        with get_connection() as connection:
            try:
                answer_status = self._feedback_repository.get_answer_status(
                    connection,
                    answer_id,
                )
                if answer_status is None:
                    raise NotFoundError(f"Answer {answer_id} was not found.")
                if answer_status != "ACTIVE":
                    raise ValidationError("Only ACTIVE answers can receive feedback.")

                existing_feedback_id = self._feedback_repository.find_feedback_id(
                    connection=connection,
                    answer_id=answer_id,
                    user_id=payload.user_id,
                )

                if existing_feedback_id is None:
                    feedback_id = self._feedback_repository.create_feedback(
                        connection=connection,
                        answer_id=answer_id,
                        user_id=payload.user_id,
                        is_like=payload.is_like,
                        rating=payload.rating,
                        comment_text=payload.comment_text,
                    )
                    operation = "CREATED"
                else:
                    existing_feedback = self._feedback_repository.get_feedback_record(
                        connection,
                        existing_feedback_id,
                    )
                    if existing_feedback is None:
                        raise NotFoundError("Existing feedback could not be reloaded.")

                    should_delete = (
                        existing_feedback["is_like"] == payload.is_like
                        and payload.rating is None
                        and payload.comment_text is None
                    )
                    if should_delete:
                        self._feedback_repository.delete_feedback(
                            connection=connection,
                            feedback_id=existing_feedback_id,
                        )
                        feedback_id = None
                        operation = "DELETED"
                    else:
                        self._feedback_repository.update_feedback(
                            connection=connection,
                            feedback_id=existing_feedback_id,
                            is_like=payload.is_like,
                            rating=payload.rating,
                            comment_text=payload.comment_text,
                        )
                        feedback_id = existing_feedback_id
                        operation = "UPDATED"

                connection.commit()
            except oracledb.DatabaseError as exc:
                connection.rollback()
                raise self._translate_database_error(exc) from exc
            except Exception:
                connection.rollback()
                raise

            feedback_record = None
            if feedback_id is not None:
                feedback_record = self._feedback_repository.get_feedback_record(
                    connection,
                    feedback_id,
                )
                if feedback_record is None:
                    raise NotFoundError("Feedback was saved but could not be reloaded.")

            answer_stats = self._feedback_repository.get_answer_feedback_stats(
                connection,
                answer_id,
            )
            if answer_stats is None:
                raise NotFoundError(
                    f"Answer {answer_id} was not found after saving feedback."
                )

        if feedback_record is None:
            feedback_record = {
                "feedback_id": None,
                "answer_id": answer_id,
                "user_id": payload.user_id,
                "is_like": None,
                "rating": None,
                "comment_text": None,
                "feedback_time": None,
            }

        return AnswerFeedbackResponse(
            **feedback_record,
            **answer_stats,
            operation=operation,
        )

    def list_question_feedbacks(
        self,
        *,
        question_id: int,
        user_id: int,
    ) -> dict[int, str]:
        if question_id <= 0:
            raise ValidationError("question_id must be greater than 0.")
        if user_id <= 0:
            raise ValidationError("user_id must be greater than 0.")

        with get_connection() as connection:
            return self._feedback_repository.list_user_feedbacks_by_question(
                connection=connection,
                question_id=question_id,
                user_id=user_id,
            )

    @staticmethod
    def _translate_database_error(exc: oracledb.DatabaseError) -> AppError:
        details = exc.args[0] if exc.args else exc
        message = getattr(details, "message", str(details))

        if "ORA-02291" in message:
            return ValidationError("user_id or answer_id contains an invalid reference.")
        if "ORA-02290" in message:
            return ValidationError("Feedback data violates a database constraint.")

        return AppError(f"Database operation failed: {message}", status_code=500)
