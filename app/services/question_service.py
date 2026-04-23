import oracledb

from app.core.errors import AppError, NotFoundError, ValidationError
from app.db.connection import get_connection
from app.repositories.answer_repository import AnswerRepository
from app.repositories.log_repository import LogRepository
from app.repositories.media_repository import MediaRepository
from app.repositories.question_repository import QuestionRepository
from app.repositories.user_repository import UserRepository
from app.schemas.question import (
    AskQuestionRequest,
    QuestionCreate,
    QuestionDetailResponse,
    QuestionListResponse,
)
from app.services.ai_answer_service import AIAnswerService


class QuestionService:
    VALID_QUESTION_STATUSES = {"OPEN", "RESOLVED", "CLOSED", "ARCHIVED"}

    def __init__(
        self,
        question_repository: QuestionRepository | None = None,
        answer_repository: AnswerRepository | None = None,
        log_repository: LogRepository | None = None,
        user_repository: UserRepository | None = None,
        media_repository: MediaRepository | None = None,
        ai_answer_service: AIAnswerService | None = None,
    ) -> None:
        self._question_repository = question_repository or QuestionRepository()
        self._answer_repository = answer_repository or AnswerRepository()
        self._log_repository = log_repository or LogRepository()
        self._user_repository = user_repository or UserRepository()
        self._media_repository = media_repository or MediaRepository()
        self._ai_answer_service = ai_answer_service or AIAnswerService()

    def ask_question(self, payload: AskQuestionRequest) -> QuestionDetailResponse:
        with get_connection() as connection:
            try:
                question_id = self._question_repository.create_question(
                    connection=connection,
                    user_id=payload.user_id,
                    category_id=payload.category_id,
                    title=payload.title,
                    content=payload.content,
                )
                self._question_repository.add_tags(
                    connection=connection,
                    question_id=question_id,
                    tag_ids=payload.tag_ids,
                )

                generated_answer = self._ai_answer_service.generate_single_answer(
                    title=payload.title,
                    content=payload.content,
                )
                self._answer_repository.create_ai_answer(
                    connection=connection,
                    question_id=question_id,
                    provider_name=generated_answer.provider_name,
                    content=generated_answer.content,
                    model_name=generated_answer.model_name,
                )
                self._log_repository.create_prompt_log(
                    connection=connection,
                    question_id=question_id,
                    prompt_text=generated_answer.prompt_text,
                    response_text=generated_answer.content,
                    token_usage=generated_answer.token_usage,
                    model_name=generated_answer.model_name,
                )

                connection.commit()
            except oracledb.DatabaseError as exc:
                connection.rollback()
                raise self._translate_database_error(exc) from exc
            except Exception:
                connection.rollback()
                raise

            question = self._question_repository.get_question_detail(connection, question_id)
            if question is None:
                raise NotFoundError("Question was created but could not be reloaded.")

            question["images"] = self._media_repository.list_active_media_by_owner(
                connection,
                owner_type="QUESTION",
                owner_id=question_id,
            )
            question["answers"] = self._answer_repository.list_answers_by_question(
                connection,
                question_id,
            )
            self._attach_answer_images(connection, question["answers"])
            return QuestionDetailResponse(**question)

    def get_question_detail(
        self,
        question_id: int,
        current_user_id: int | None = None,
    ) -> QuestionDetailResponse:
        if question_id <= 0:
            raise ValidationError("question_id must be greater than 0.")

        with get_connection() as connection:
            question = self._question_repository.get_question_detail(
                connection,
                question_id,
                current_user_id=current_user_id,
            )
            if question is None:
                raise NotFoundError(f"Question {question_id} was not found.")

            question["images"] = self._media_repository.list_active_media_by_owner(
                connection,
                owner_type="QUESTION",
                owner_id=question_id,
            )
            question["answers"] = self._answer_repository.list_answers_by_question(
                connection,
                question_id,
            )
            self._attach_answer_images(connection, question["answers"])
            return QuestionDetailResponse(**question)

    def list_questions(
        self,
        *,
        page: int = 1,
        page_size: int = 10,
        category_id: int | None = None,
        tag_id: int | None = None,
        status: str | None = "OPEN",
        current_user_id: int | None = None,
    ) -> QuestionListResponse:
        if page <= 0:
            raise ValidationError("page must be greater than 0.")
        if page_size <= 0 or page_size > 50:
            raise ValidationError("page_size must be between 1 and 50.")
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

        with get_connection() as connection:
            items = self._question_repository.list_questions(
                connection=connection,
                page=page,
                page_size=page_size,
                category_id=category_id,
                tag_id=tag_id,
                status=normalized_status,
                current_user_id=current_user_id,
            )
            total = self._question_repository.count_questions(
                connection=connection,
                category_id=category_id,
                tag_id=tag_id,
                status=normalized_status,
            )

        return QuestionListResponse(
            items=items,
            page=page,
            page_size=page_size,
            total=total,
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
            return ValidationError("user_id, category_id, or tag_ids contain invalid references.")
        if "ORA-00001" in message:
            return ValidationError("Duplicate question-tag relationship was detected.")
        if "ORA-2290" in message:
            return ValidationError("Request data violates a database constraint.")

        return AppError(f"Database operation failed: {message}", status_code=500)

    def publish_question(self, user_id: int, payload: QuestionCreate) -> dict:
        with get_connection() as connection:
            default_category_id = self._question_repository.get_first_active_category_id(connection)
            if default_category_id is None:
                raise ValidationError("No ACTIVE category is available for publishing questions.")

            q_id = self._question_repository.create_question(
                connection=connection,
                user_id=user_id,
                category_id=default_category_id,
                title=payload.title,
                content=payload.content,
            )
            connection.commit()
            return {"question_id": q_id, "message": "发布成功"}

    def accept_answer(
        self,
        *,
        question_id: int,
        answer_id: int,
        current_user_id: int,
    ) -> QuestionDetailResponse:
        if question_id <= 0:
            raise ValidationError("question_id must be greater than 0.")
        if answer_id <= 0:
            raise ValidationError("answer_id must be greater than 0.")
        if current_user_id <= 0:
            raise ValidationError("current_user_id must be greater than 0.")

        with get_connection() as connection:
            question = self._question_repository.get_question_acceptance_context(
                connection,
                question_id,
            )
            if question is None:
                raise NotFoundError(f"Question {question_id} was not found.")

            current_user = self._user_repository.get_user_by_id(connection, current_user_id)
            if current_user is None:
                raise AppError("当前登录用户不存在，请重新登录。", status_code=401)

            is_owner = question["user_id"] == current_user_id
            is_admin = current_user["role"] == "ADMIN"
            if not (is_owner or is_admin):
                raise AppError("只有提问者或管理员可以采纳答案。", status_code=403)

            if question["status"] in {"CLOSED", "ARCHIVED"}:
                raise ValidationError("CLOSED 或 ARCHIVED 状态的问题不能再采纳答案。")

            answer = self._answer_repository.get_answer_context(connection, answer_id)
            if answer is None:
                raise NotFoundError(f"Answer {answer_id} was not found.")
            if answer["question_id"] != question_id:
                raise ValidationError("answer_id 不属于当前问题，不能被采纳。")
            if answer["answer_type"] == "SYSTEM":
                raise ValidationError("SYSTEM 类型回答不能被采纳。")

            try:
                updated_count = self._question_repository.accept_answer(
                    connection=connection,
                    question_id=question_id,
                    answer_id=answer_id,
                )
                connection.commit()
            except oracledb.DatabaseError as exc:
                connection.rollback()
                raise self._translate_database_error(exc) from exc
            except Exception:
                connection.rollback()
                raise

            if updated_count == 0:
                raise NotFoundError(f"Question {question_id} could not be updated.")

            refreshed_question = self._question_repository.get_question_detail(
                connection,
                question_id,
                current_user_id=current_user_id,
            )
            if refreshed_question is None:
                raise NotFoundError("Answer was accepted but the question could not be reloaded.")

            refreshed_question["answers"] = self._answer_repository.list_answers_by_question(
                connection,
                question_id,
            )
            refreshed_question["images"] = self._media_repository.list_active_media_by_owner(
                connection,
                owner_type="QUESTION",
                owner_id=question_id,
            )
            self._attach_answer_images(connection, refreshed_question["answers"])

        return QuestionDetailResponse(**refreshed_question)
