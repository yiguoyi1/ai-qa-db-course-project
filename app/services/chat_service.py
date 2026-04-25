import oracledb

from app.core.errors import AppError, NotFoundError, ValidationError
from app.db.connection import get_connection
from app.repositories.answer_repository import AnswerRepository
from app.repositories.chat_repository import ChatRepository
from app.repositories.log_repository import LogRepository
from app.repositories.question_repository import QuestionRepository
from app.schemas.chat import (
    ChatSessionDetailResponse,
    ChatSessionItem,
    ChatSessionListResponse,
    CreateFollowUpTurnRequest,
)
from app.services.ai_answer_service import AIAnswerService


class ChatService:
    MAX_CONTEXT_MESSAGES = 12

    def __init__(
        self,
        *,
        chat_repository: ChatRepository | None = None,
        question_repository: QuestionRepository | None = None,
        answer_repository: AnswerRepository | None = None,
        log_repository: LogRepository | None = None,
        ai_answer_service: AIAnswerService | None = None,
    ) -> None:
        self._chat_repository = chat_repository or ChatRepository()
        self._question_repository = question_repository or QuestionRepository()
        self._answer_repository = answer_repository or AnswerRepository()
        self._log_repository = log_repository or LogRepository()
        self._ai_answer_service = ai_answer_service or AIAnswerService()

    def create_follow_up_turn(
        self,
        *,
        question_id: int,
        answer_id: int,
        current_user_id: int,
        payload: CreateFollowUpTurnRequest,
    ) -> ChatSessionDetailResponse:
        if question_id <= 0:
            raise ValidationError("question_id must be greater than 0.")
        if answer_id <= 0:
            raise ValidationError("answer_id must be greater than 0.")
        if current_user_id <= 0:
            raise ValidationError("current_user_id must be greater than 0.")

        user_content = payload.content.strip()
        if not user_content:
            raise ValidationError("content must not be blank.")

        with get_connection() as connection:
            question = self._question_repository.get_question_detail(connection, question_id)
            if question is None:
                raise NotFoundError(f"Question {question_id} was not found.")

            seed_answer = self._answer_repository.get_answer_by_id(connection, answer_id)
            if seed_answer is None:
                raise NotFoundError(f"Answer {answer_id} was not found.")
            if seed_answer["question_id"] != question_id:
                raise ValidationError("answer_id does not belong to the given question.")
            if seed_answer["answer_type"] != "AI":
                raise ValidationError("当前多轮追问仅支持基于 AI 回答发起。")

            try:
                session = self._resolve_or_create_session(
                    connection=connection,
                    session_id=payload.session_id,
                    current_user_id=current_user_id,
                    question_id=question_id,
                    answer_id=answer_id,
                )

                self._chat_repository.create_message(
                    connection,
                    session_id=session["session_id"],
                    sender_type="USER",
                    content=user_content,
                )

                history_messages = self._chat_repository.list_messages_by_session(
                    connection,
                    session_id=session["session_id"],
                    limit=self.MAX_CONTEXT_MESSAGES,
                )

                generated_answer = self._ai_answer_service.generate_follow_up_answer(
                    title=question["title"],
                    content=question["content"],
                    seed_answer_content=seed_answer["content"],
                    history_messages=history_messages,
                )

                self._chat_repository.create_message(
                    connection,
                    session_id=session["session_id"],
                    sender_type="AI",
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

            return self.get_session_detail(
                session_id=session["session_id"],
                current_user_id=current_user_id,
            )

    def get_session_detail(
        self,
        *,
        session_id: int,
        current_user_id: int,
    ) -> ChatSessionDetailResponse:
        if session_id <= 0:
            raise ValidationError("session_id must be greater than 0.")
        if current_user_id <= 0:
            raise ValidationError("current_user_id must be greater than 0.")

        with get_connection() as connection:
            session = self._chat_repository.get_session_by_id(connection, session_id)
            if session is None:
                raise NotFoundError(f"Session {session_id} was not found.")

            messages = self._chat_repository.list_messages_by_session(
                connection,
                session_id=session_id,
            )

        return ChatSessionDetailResponse(
            session=ChatSessionItem(**session),
            messages=messages,
        )

    def list_sessions_by_anchor(
        self,
        *,
        question_id: int,
        answer_id: int,
        current_user_id: int,
    ) -> ChatSessionListResponse:
        if question_id <= 0:
            raise ValidationError("question_id must be greater than 0.")
        if answer_id <= 0:
            raise ValidationError("answer_id must be greater than 0.")
        if current_user_id <= 0:
            raise ValidationError("current_user_id must be greater than 0.")

        with get_connection() as connection:
            seed_answer = self._answer_repository.get_answer_by_id(connection, answer_id)
            if seed_answer is None:
                raise NotFoundError(f"Answer {answer_id} was not found.")
            if seed_answer["question_id"] != question_id:
                raise ValidationError("answer_id does not belong to the given question.")

            items = self._chat_repository.list_sessions_by_anchor(
                connection,
                question_id=question_id,
                seed_answer_id=answer_id,
            )

        return ChatSessionListResponse(
            question_id=question_id,
            seed_answer_id=answer_id,
            item_count=len(items),
            items=[ChatSessionItem(**item) for item in items],
        )

    def _resolve_or_create_session(
        self,
        *,
        connection: oracledb.Connection,
        session_id: int | None,
        current_user_id: int,
        question_id: int,
        answer_id: int,
    ) -> dict:
        if session_id is None:
            created_session_id = self._chat_repository.create_session(
                connection,
                user_id=current_user_id,
                question_id=question_id,
                seed_answer_id=answer_id,
            )
            session = self._chat_repository.get_session_by_id(connection, created_session_id)
            assert session is not None
            return session

        session = self._chat_repository.get_session_by_id(connection, session_id)
        if session is None:
            raise NotFoundError(f"Session {session_id} was not found.")
        if session["user_id"] != current_user_id:
            raise ValidationError("当前用户不能续写别人的 AI 会话。")
        if session["question_id"] != question_id or session["seed_answer_id"] != answer_id:
            raise ValidationError("session_id 与当前问题或 AI 回答不匹配。")
        if session["status"] != "OPEN":
            raise ValidationError("当前 AI 会话已关闭，不能继续追问。")
        return session

    @staticmethod
    def _translate_database_error(exc: oracledb.DatabaseError) -> AppError:
        details = exc.args[0] if exc.args else exc
        message = getattr(details, "message", str(details))

        if "ORA-02291" in message:
            return ValidationError("chat session references invalid question, answer, or user data.")
        if "ORA-02290" in message:
            return ValidationError("chat session data violates a database constraint.")

        return AppError(f"Database operation failed: {message}", status_code=500)
