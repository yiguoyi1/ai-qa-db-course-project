import re

import oracledb

from app.core.category_catalog import DEFAULT_CATEGORY_NAME
from app.core.errors import AppError, NotFoundError, ValidationError
from app.db.connection import get_connection
from app.repositories.answer_repository import AnswerRepository
from app.repositories.log_repository import LogRepository
from app.repositories.media_repository import MediaRepository
from app.repositories.question_repository import QuestionRepository
from app.repositories.tag_repository import TagRepository
from app.repositories.user_repository import UserRepository
from app.schemas.question import (
    AskQuestionRequest,
    QuestionCreate,
    QuestionDeleteResponse,
    QuestionDetailResponse,
    QuestionListResponse,
)
from app.services.ai_answer_service import AIAnswerService
from app.services.ai_category_service import AICategoryService, GeneratedCategory
from app.services.ai_tagging_service import AITaggingService, GeneratedTags


class QuestionService:
    VALID_QUESTION_STATUSES = {"OPEN", "RESOLVED", "CLOSED", "ARCHIVED"}
    MAX_QUESTION_TAGS = 10

    def __init__(
        self,
        question_repository: QuestionRepository | None = None,
        answer_repository: AnswerRepository | None = None,
        log_repository: LogRepository | None = None,
        user_repository: UserRepository | None = None,
        media_repository: MediaRepository | None = None,
        tag_repository: TagRepository | None = None,
        ai_answer_service: AIAnswerService | None = None,
        ai_category_service: AICategoryService | None = None,
        ai_tagging_service: AITaggingService | None = None,
    ) -> None:
        self._question_repository = question_repository or QuestionRepository()
        self._answer_repository = answer_repository or AnswerRepository()
        self._log_repository = log_repository or LogRepository()
        self._user_repository = user_repository or UserRepository()
        self._media_repository = media_repository or MediaRepository()
        self._tag_repository = tag_repository or TagRepository()
        self._ai_answer_service = ai_answer_service
        self._ai_category_service = ai_category_service
        self._ai_tagging_service = ai_tagging_service

    def ask_question(self, payload: AskQuestionRequest) -> QuestionDetailResponse:
        if payload.user_id is None:
            raise ValidationError("user_id is required.")

        with get_connection() as connection:
            try:
                category_id, generated_category = self._resolve_category_id(
                    connection=connection,
                    requested_category_id=payload.category_id,
                    auto_category=payload.auto_category,
                    title=payload.title,
                    content=payload.content,
                )
                question_id = self._question_repository.create_question(
                    connection=connection,
                    user_id=payload.user_id,
                    category_id=category_id,
                    title=payload.title,
                    content=payload.content,
                )
                self._log_ai_category_result(
                    connection=connection,
                    question_id=question_id,
                    generated_category=generated_category,
                )
                self._attach_question_tags(
                    connection=connection,
                    question_id=question_id,
                    user_id=int(payload.user_id),
                    title=payload.title,
                    content=payload.content,
                    tag_ids=payload.tag_ids,
                    custom_tags=payload.custom_tags,
                    auto_tag=payload.auto_tag,
                )

                generated_answer = self._get_ai_answer_service().generate_single_answer(
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

    def generate_ai_answer_for_question(
        self,
        *,
        question_id: int,
        current_user_id: int,
    ) -> QuestionDetailResponse:
        if question_id <= 0:
            raise ValidationError("question_id must be greater than 0.")

        with get_connection() as connection:
            try:
                question = self._question_repository.get_question_detail(
                    connection,
                    question_id,
                    current_user_id=current_user_id,
                )
                if question is None or question["status"] == "DELETED":
                    raise NotFoundError(f"Question {question_id} was not found.")
                if int(question["user_id"]) != int(current_user_id):
                    raise ValidationError("只有问题作者可以为该问题生成 AI 首答。")

                images = self._media_repository.list_active_media_by_owner(
                    connection,
                    owner_type="QUESTION",
                    owner_id=question_id,
                )
                generated_answer = self._get_ai_answer_service().generate_single_answer(
                    title=question["title"],
                    content=question["content"],
                    image_contexts=self._build_question_image_contexts(images),
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

            refreshed_question = self._question_repository.get_question_detail(
                connection,
                question_id,
                current_user_id=current_user_id,
            )
            if refreshed_question is None:
                raise NotFoundError("AI answer was created but the question could not be reloaded.")

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
            if question["status"] == "DELETED" and question["user_id"] != current_user_id:
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
        include_total: bool = True,
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
            if include_total:
                total = self._question_repository.count_questions(
                    connection=connection,
                    category_id=category_id,
                    tag_id=tag_id,
                    status=normalized_status,
                )
            else:
                total = (page - 1) * page_size + len(items)

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
    def _build_question_image_contexts(images: list[dict]) -> list[str]:
        contexts: list[str] = []
        for index, image in enumerate(images, start=1):
            name = image.get("original_file_name") or image.get("file_name") or f"图片 {index}"
            mime_type = image.get("mime_type") or "未知格式"
            public_url = image.get("public_url") or ""
            size = image.get("file_size")
            size_text = f"，大小 {int(size)} 字节" if size is not None else ""
            url_text = f"，链接：{public_url}" if public_url else ""
            contexts.append(f"第 {index} 张：文件名 {name}，格式 {mime_type}{size_text}{url_text}")
        return contexts

    def _attach_question_tags(
        self,
        *,
        connection: oracledb.Connection,
        question_id: int,
        user_id: int,
        title: str,
        content: str,
        tag_ids: list[int],
        custom_tags: list[str],
        auto_tag: bool,
    ) -> None:
        selected_tag_ids = self._normalize_tag_ids(tag_ids)
        bound_tag_ids: set[int] = set()

        if selected_tag_ids:
            selected_tags = self._tag_repository.get_tags_by_ids(connection, selected_tag_ids)
            unavailable_tag_ids = [
                tag_id
                for tag_id in selected_tag_ids
                if tag_id not in selected_tags or selected_tags[tag_id]["status"] != "ACTIVE"
            ]
            if unavailable_tag_ids:
                raise ValidationError("tag_ids contain invalid or unavailable tags.")

            self._question_repository.add_tags(
                connection=connection,
                question_id=question_id,
                tag_ids=selected_tag_ids,
                source="USER_SELECTED",
            )
            bound_tag_ids.update(selected_tag_ids)

        for tag_name in self._normalize_custom_tags(custom_tags):
            if len(bound_tag_ids) >= self.MAX_QUESTION_TAGS:
                raise ValidationError(f"A question can have at most {self.MAX_QUESTION_TAGS} tags.")

            tag = self._tag_repository.get_tag_by_name(connection, tag_name)
            if tag is not None and tag["status"] != "ACTIVE":
                raise ValidationError(f"Tag '{tag_name}' is not available.")
            tag_id = (
                int(tag["tag_id"])
                if tag is not None
                else self._tag_repository.create_tag(
                    connection,
                    tag_name=tag_name,
                    source="USER",
                    create_user_id=user_id,
                )
            )
            if tag_id in bound_tag_ids:
                continue

            self._question_repository.add_tags(
                connection=connection,
                question_id=question_id,
                tag_ids=[tag_id],
                source="USER_CREATED",
            )
            bound_tag_ids.add(tag_id)

        if bound_tag_ids or not auto_tag:
            return

        generated_tags = self._generate_ai_tags(
            connection=connection,
            title=title,
            content=content,
        )
        if generated_tags is None:
            return

        if generated_tags.prompt_text:
            self._log_repository.create_prompt_log(
                connection=connection,
                question_id=question_id,
                prompt_text=generated_tags.prompt_text,
                response_text=generated_tags.response_text,
                token_usage=generated_tags.token_usage,
                model_name=generated_tags.model_name,
            )

        for candidate in generated_tags.candidates:
            if len(bound_tag_ids) >= self.MAX_QUESTION_TAGS:
                break

            tag_id = candidate.tag_id
            source = candidate.source
            if tag_id is None:
                tag = self._tag_repository.get_tag_by_name(connection, candidate.tag_name)
                if tag is not None:
                    if tag["status"] != "ACTIVE":
                        continue
                    tag_id = int(tag["tag_id"])
                    source = "AI_MATCHED"
                else:
                    tag_id = self._tag_repository.create_tag(
                        connection,
                        tag_name=candidate.tag_name,
                        source="AI",
                        create_user_id=user_id,
                        description=generated_tags.reason[:200] or None,
                    )
                    source = "AI_CREATED"

            if tag_id in bound_tag_ids:
                continue

            self._question_repository.add_tags(
                connection=connection,
                question_id=question_id,
                tag_ids=[tag_id],
                source=source,
                confidence_score=candidate.confidence_score,
            )
            bound_tag_ids.add(tag_id)

    def _generate_ai_tags(
        self,
        *,
        connection: oracledb.Connection,
        title: str,
        content: str,
    ) -> GeneratedTags | None:
        existing_tags = self._tag_repository.list_active_tags(connection)
        try:
            return self._get_ai_tagging_service().analyze_question_tags(
                title=title,
                content=content,
                existing_tags=existing_tags,
            )
        except Exception:
            return None

    def _resolve_category_id(
        self,
        *,
        connection: oracledb.Connection,
        requested_category_id: int | None,
        auto_category: bool,
        title: str,
        content: str,
    ) -> tuple[int, GeneratedCategory | None]:
        active_categories = self._question_repository.list_active_categories(connection)
        if not active_categories:
            raise ValidationError("当前没有可用分类，请联系管理员先启用或创建分类。")

        default_category_id = self._get_default_category_id(active_categories)
        if requested_category_id is not None:
            requested_category = self._question_repository.get_active_category_context(
                connection,
                requested_category_id,
            )
            if requested_category is None:
                raise ValidationError("所选分类不存在或已停用，请重新选择分类。")

        should_ai_classify = auto_category and (
            requested_category_id is None
            or requested_category_id == default_category_id
        )
        if not should_ai_classify:
            return requested_category_id or default_category_id, None

        generated_category = self._generate_ai_category(
            title=title,
            content=content,
            active_categories=active_categories,
        )
        if generated_category is None:
            return requested_category_id or default_category_id, None

        return generated_category.category_id, generated_category

    def _generate_ai_category(
        self,
        *,
        title: str,
        content: str,
        active_categories: list[dict],
    ) -> GeneratedCategory | None:
        try:
            return self._get_ai_category_service().classify_question(
                title=title,
                content=content,
                active_categories=active_categories,
            )
        except Exception:
            return None

    @staticmethod
    def _get_default_category_id(active_categories: list[dict]) -> int:
        for category in active_categories:
            if category["category_name"] == DEFAULT_CATEGORY_NAME:
                return int(category["category_id"])
        return int(active_categories[0]["category_id"])

    def _log_ai_category_result(
        self,
        *,
        connection: oracledb.Connection,
        question_id: int,
        generated_category: GeneratedCategory | None,
    ) -> None:
        if generated_category is None or not generated_category.prompt_text:
            return

        response_text = generated_category.response_text
        if generated_category.reason:
            response_text = (
                f"{response_text}\n\n"
                f"selected_category={generated_category.category_name}, "
                f"confidence={generated_category.confidence_score}, "
                f"reason={generated_category.reason}"
            )

        self._log_repository.create_prompt_log(
            connection=connection,
            question_id=question_id,
            prompt_text=generated_category.prompt_text,
            response_text=response_text,
            token_usage=generated_category.token_usage,
            model_name=generated_category.model_name,
        )

    def _get_ai_answer_service(self) -> AIAnswerService:
        if self._ai_answer_service is None:
            self._ai_answer_service = AIAnswerService()
        return self._ai_answer_service

    def _get_ai_category_service(self) -> AICategoryService:
        if self._ai_category_service is None:
            self._ai_category_service = AICategoryService()
        return self._ai_category_service

    def _get_ai_tagging_service(self) -> AITaggingService:
        if self._ai_tagging_service is None:
            self._ai_tagging_service = AITaggingService()
        return self._ai_tagging_service

    @classmethod
    def _normalize_tag_ids(cls, tag_ids: list[int]) -> list[int]:
        normalized: list[int] = []
        seen: set[int] = set()

        for raw_tag_id in tag_ids:
            try:
                tag_id = int(raw_tag_id)
            except (TypeError, ValueError):
                raise ValidationError("标签参数不正确，请重新选择标签。") from None
            if tag_id <= 0:
                raise ValidationError("标签参数不正确，请重新选择标签。")
            if tag_id in seen:
                continue
            if len(normalized) >= cls.MAX_QUESTION_TAGS:
                raise ValidationError(f"每个问题最多只能添加 {cls.MAX_QUESTION_TAGS} 个标签。")
            seen.add(tag_id)
            normalized.append(tag_id)

        return normalized

    @classmethod
    def _normalize_custom_tags(cls, custom_tags: list[str]) -> list[str]:
        normalized: list[str] = []
        seen: set[str] = set()

        for raw_tag_name in custom_tags:
            tag_name = cls._normalize_tag_name(raw_tag_name)
            if not tag_name:
                continue
            key = tag_name.casefold()
            if key in seen:
                continue
            if len(normalized) >= cls.MAX_QUESTION_TAGS:
                raise ValidationError(f"A question can have at most {cls.MAX_QUESTION_TAGS} tags.")
            seen.add(key)
            normalized.append(tag_name)

        return normalized

    @staticmethod
    def _normalize_tag_name(tag_name: str) -> str:
        normalized = re.sub(r"\s+", "-", tag_name.strip().lstrip("#"))
        normalized = normalized.strip("-").lower()
        if len(normalized) > 50:
            normalized = normalized[:50].strip("-")
        return normalized

    @staticmethod
    def _translate_database_error(exc: oracledb.DatabaseError) -> AppError:
        details = exc.args[0] if exc.args else exc
        message = getattr(details, "message", str(details))

        if "ORA-02291" in message:
            return ValidationError("发布参数包含无效的用户、分类或标签，请刷新页面后重试。")
        if "ORA-00001" in message:
            return ValidationError("问题标签重复，请刷新页面后重试。")
        if "ORA-02290" in message or "ORA-2290" in message:
            return ValidationError("发布内容不符合数据库约束，请检查标题、正文、分类和标签。")

        return AppError(f"Database operation failed: {message}", status_code=500)

    def publish_question(self, user_id: int, payload: QuestionCreate) -> dict:
        with get_connection() as connection:
            try:
                category_id, generated_category = self._resolve_category_id(
                    connection=connection,
                    requested_category_id=payload.category_id,
                    auto_category=payload.auto_category,
                    title=payload.title,
                    content=payload.content,
                )

                question_id = self._question_repository.create_question(
                    connection=connection,
                    user_id=user_id,
                    category_id=category_id,
                    title=payload.title,
                    content=payload.content,
                )
                self._log_ai_category_result(
                    connection=connection,
                    question_id=question_id,
                    generated_category=generated_category,
                )
                self._attach_question_tags(
                    connection=connection,
                    question_id=question_id,
                    user_id=user_id,
                    title=payload.title,
                    content=payload.content,
                    tag_ids=payload.tag_ids,
                    custom_tags=payload.custom_tags,
                    auto_tag=payload.auto_tag,
                )
                connection.commit()
            except oracledb.DatabaseError as exc:
                connection.rollback()
                raise self._translate_database_error(exc) from exc
            except Exception:
                connection.rollback()
                raise

            return {"question_id": question_id, "message": "published"}

    def delete_question(
        self,
        *,
        question_id: int,
        current_user_id: int,
    ) -> QuestionDeleteResponse:
        if question_id <= 0:
            raise ValidationError("question_id must be greater than 0.")
        if current_user_id <= 0:
            raise ValidationError("current_user_id must be greater than 0.")

        with get_connection() as connection:
            question = self._question_repository.get_question_context(
                connection,
                question_id,
            )
            if question is None:
                raise NotFoundError(f"Question {question_id} was not found.")
            if question["user_id"] != current_user_id:
                raise AppError("Only the question author can delete this question.", status_code=403)
            if question["status"] == "DELETED":
                raise ValidationError("Question has already been deleted.")

            try:
                updated_count = self._question_repository.update_question_status(
                    connection=connection,
                    question_id=question_id,
                    status="DELETED",
                )
                if updated_count == 0:
                    raise NotFoundError(f"Question {question_id} could not be deleted.")

                self._log_repository.create_operation_log(
                    connection,
                    user_id=current_user_id,
                    op_type="AUTHOR_DELETE_QUESTION",
                    op_content=(
                        f"question_id={question_id}, title={question['title']}, "
                        f"from={question['status']}, to=DELETED"
                    ),
                )
                connection.commit()
            except oracledb.DatabaseError as exc:
                connection.rollback()
                raise self._translate_database_error(exc) from exc
            except Exception:
                connection.rollback()
                raise

        return QuestionDeleteResponse(
            question_id=question_id,
            status="DELETED",
            message="Question deleted successfully.",
        )

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

            if question["status"] in {"CLOSED", "ARCHIVED", "DELETED"}:
                raise ValidationError("CLOSED、ARCHIVED 或 DELETED 状态的问题不能再采纳答案。")

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
