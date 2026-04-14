import oracledb

from app.core.errors import AppError, NotFoundError, ValidationError
from app.db.connection import get_connection
from app.repositories.answer_repository import AnswerRepository
from app.repositories.question_repository import QuestionRepository
from app.schemas.answer import CreateManualAnswerRequest
from app.schemas.question import QuestionDetailResponse


class AnswerService:
    def __init__(
        self,
        answer_repository: AnswerRepository | None = None,
        question_repository: QuestionRepository | None = None,
    ) -> None:
        self._answer_repository = answer_repository or AnswerRepository()
        self._question_repository = question_repository or QuestionRepository()

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

            refreshed_question["answers"] = self._answer_repository.list_answers_by_question(
                connection,
                question_id,
            )

        return QuestionDetailResponse(**refreshed_question)

    @staticmethod
    def _translate_database_error(exc: oracledb.DatabaseError) -> AppError:
        details = exc.args[0] if exc.args else exc
        message = getattr(details, "message", str(details))

        if "ORA-02291" in message:
            return ValidationError("user_id or question_id contains an invalid reference.")
        if "ORA-02290" in message:
            return ValidationError("Manual answer data violates a database constraint.")

        return AppError(f"Database operation failed: {message}", status_code=500)

    # 🌟 新增：处理点赞/踩请求
    def submit_feedback(self, answer_id: int, user_id: int, is_like: str) -> dict:
        with get_connection() as connection:
            action = self._answer_repository.handle_feedback(connection, answer_id, user_id, is_like)
            connection.commit()
            return {"message": "反馈成功", "action": action, "is_like": is_like}

    # 🌟 新增：获取用户的反馈状态
    def get_user_feedbacks(self, question_id: int, user_id: int) -> dict:
        with get_connection() as connection:
            return self._answer_repository.get_user_feedbacks_for_question(connection, question_id, user_id)
