from app.core.errors import NotFoundError, ValidationError
from app.db.connection import get_connection
from app.repositories.admin_repository import AdminRepository
from app.repositories.log_repository import LogRepository
from app.schemas.admin import (
    AdminCategoryListResponse,
    AdminCategoryMutationResponse,
    AdminCommentStatusResponse,
    AdminLoginLogListResponse,
    AdminOperationLogListResponse,
    AdminQuestionStatusResponse,
    AdminTagListResponse,
    AdminTagMutationResponse,
    AdminUserListResponse,
    AdminUserMutationResponse,
)


class AdminService:
    VALID_CATEGORY_STATUSES = {"ACTIVE", "INACTIVE"}
    VALID_LOGIN_RESULTS = {"SUCCESS", "FAILURE", "LOCKED"}
    VALID_USER_ROLES = {"USER", "ADMIN"}
    VALID_USER_STATUSES = {"ACTIVE", "INACTIVE", "LOCKED", "DISABLED"}
    VALID_QUESTION_STATUSES = {"OPEN", "RESOLVED", "CLOSED", "ARCHIVED"}
    VALID_COMMENT_STATUSES = {"ACTIVE", "HIDDEN"}
    VALID_TAG_SOURCES = {"SYSTEM", "USER", "AI", "ADMIN"}
    VALID_TAG_STATUSES = {"ACTIVE", "PENDING", "DISABLED"}

    def __init__(
        self,
        admin_repository: AdminRepository | None = None,
        log_repository: LogRepository | None = None,
    ) -> None:
        self._admin_repository = admin_repository or AdminRepository()
        self._log_repository = log_repository or LogRepository()

    def list_users(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        role: str | None = None,
        status: str | None = None,
    ) -> AdminUserListResponse:
        if page <= 0:
            raise ValidationError("page must be greater than 0.")
        if page_size <= 0 or page_size > 100:
            raise ValidationError("page_size must be between 1 and 100.")

        normalized_role = self._normalize_enum(role)
        normalized_status = self._normalize_enum(status)

        if normalized_role is not None and normalized_role not in self.VALID_USER_ROLES:
            raise ValidationError("role must be USER or ADMIN.")
        if normalized_status is not None and normalized_status not in self.VALID_USER_STATUSES:
            raise ValidationError("status must be ACTIVE, INACTIVE, LOCKED, or DISABLED.")

        with get_connection() as connection:
            items = self._admin_repository.list_users(
                connection,
                page=page,
                page_size=page_size,
                role=normalized_role,
                status=normalized_status,
            )
            total = self._admin_repository.count_users(
                connection,
                role=normalized_role,
                status=normalized_status,
            )

        return AdminUserListResponse(
            items=items,
            page=page,
            page_size=page_size,
            total=total,
        )

    def list_categories(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        status: str | None = None,
    ) -> AdminCategoryListResponse:
        if page <= 0:
            raise ValidationError("page must be greater than 0.")
        if page_size <= 0 or page_size > 100:
            raise ValidationError("page_size must be between 1 and 100.")

        normalized_status = self._normalize_enum(status)
        if (
            normalized_status is not None
            and normalized_status not in self.VALID_CATEGORY_STATUSES
        ):
            raise ValidationError("status must be ACTIVE or INACTIVE.")

        with get_connection() as connection:
            items = self._admin_repository.list_categories(
                connection,
                page=page,
                page_size=page_size,
                status=normalized_status,
            )
            total = self._admin_repository.count_categories(
                connection,
                status=normalized_status,
            )

        return AdminCategoryListResponse(
            items=items,
            page=page,
            page_size=page_size,
            total=total,
        )

    def create_category(
        self,
        *,
        admin_user_id: int,
        category_name: str,
        description: str | None,
        status: str,
    ) -> AdminCategoryMutationResponse:
        normalized_name = self._require_category_name(category_name)
        normalized_description = self._normalize_description(description)
        normalized_status = self._require_category_status(status)

        with get_connection() as connection:
            existing_category = self._admin_repository.get_category_by_name(
                connection,
                normalized_name,
            )
            if existing_category is not None:
                raise ValidationError("Category name already exists.")

            category_id = self._admin_repository.create_category(
                connection,
                category_name=normalized_name,
                description=normalized_description,
                status=normalized_status,
            )

            self._log_repository.create_operation_log(
                connection,
                user_id=admin_user_id,
                op_type="ADMIN_CREATE_CATEGORY",
                op_content=(
                    f"category_id={category_id}, category_name={normalized_name}, "
                    f"status={normalized_status}"
                ),
            )
            connection.commit()

            category = self._admin_repository.get_category_context(connection, category_id)
            assert category is not None

        return AdminCategoryMutationResponse(
            category_id=category["category_id"],
            category_name=category["category_name"],
            description=category["description"],
            status=category["status"],
            message="Category created successfully.",
        )

    def update_category(
        self,
        *,
        admin_user_id: int,
        category_id: int,
        category_name: str | None,
        description: str | None,
        status: str | None,
    ) -> AdminCategoryMutationResponse:
        with get_connection() as connection:
            current_category = self._admin_repository.get_category_context(connection, category_id)
            if current_category is None:
                raise NotFoundError(f"Category {category_id} was not found.")

            next_name = (
                self._require_category_name(category_name)
                if category_name is not None
                else current_category["category_name"]
            )
            next_description = (
                self._normalize_description(description)
                if description is not None
                else current_category["description"]
            )
            next_status = (
                self._require_category_status(status)
                if status is not None
                else current_category["status"]
            )

            duplicate_category = self._admin_repository.get_category_by_name(
                connection,
                next_name,
            )
            if (
                duplicate_category is not None
                and duplicate_category["category_id"] != category_id
            ):
                raise ValidationError("Category name already exists.")

            if (
                current_category["category_name"] == next_name
                and current_category["description"] == next_description
                and current_category["status"] == next_status
            ):
                raise ValidationError("No category fields changed.")

            updated_count = self._admin_repository.update_category(
                connection,
                category_id=category_id,
                category_name=next_name,
                description=next_description,
                status=next_status,
            )
            if updated_count == 0:
                raise NotFoundError(f"Category {category_id} could not be updated.")

            self._log_repository.create_operation_log(
                connection,
                user_id=admin_user_id,
                op_type="ADMIN_UPDATE_CATEGORY",
                op_content=(
                    f"category_id={category_id}, "
                    f"name={current_category['category_name']}->{next_name}, "
                    f"status={current_category['status']}->{next_status}"
                ),
            )
            connection.commit()

            refreshed_category = self._admin_repository.get_category_context(connection, category_id)
            assert refreshed_category is not None

        return AdminCategoryMutationResponse(
            category_id=refreshed_category["category_id"],
            category_name=refreshed_category["category_name"],
            description=refreshed_category["description"],
            status=refreshed_category["status"],
            message="Category updated successfully.",
        )

    def list_tags(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        source: str | None = None,
        status: str | None = None,
        keyword: str | None = None,
    ) -> AdminTagListResponse:
        if page <= 0:
            raise ValidationError("page must be greater than 0.")
        if page_size <= 0 or page_size > 100:
            raise ValidationError("page_size must be between 1 and 100.")

        normalized_source = self._normalize_enum(source)
        normalized_status = self._normalize_enum(status)
        normalized_keyword = self._normalize_keyword(keyword)

        if normalized_source is not None and normalized_source not in self.VALID_TAG_SOURCES:
            raise ValidationError("source must be SYSTEM, USER, AI, or ADMIN.")
        if normalized_status is not None and normalized_status not in self.VALID_TAG_STATUSES:
            raise ValidationError("status must be ACTIVE, PENDING, or DISABLED.")

        with get_connection() as connection:
            items = self._admin_repository.list_tags(
                connection,
                page=page,
                page_size=page_size,
                source=normalized_source,
                status=normalized_status,
                keyword=normalized_keyword,
            )
            total = self._admin_repository.count_tags(
                connection,
                source=normalized_source,
                status=normalized_status,
                keyword=normalized_keyword,
            )

        return AdminTagListResponse(
            items=items,
            page=page,
            page_size=page_size,
            total=total,
        )

    def update_tag(
        self,
        *,
        admin_user_id: int,
        tag_id: int,
        tag_name: str | None,
        description: str | None,
        status: str | None,
    ) -> AdminTagMutationResponse:
        if tag_id <= 0:
            raise ValidationError("tag_id must be greater than 0.")

        with get_connection() as connection:
            current_tag = self._admin_repository.get_tag_context(connection, tag_id)
            if current_tag is None:
                raise NotFoundError(f"Tag {tag_id} was not found.")

            next_name = (
                self._require_tag_name(tag_name)
                if tag_name is not None
                else current_tag["tag_name"]
            )
            next_description = (
                self._normalize_description(description)
                if description is not None
                else current_tag["description"]
            )
            next_status = (
                self._require_tag_status(status)
                if status is not None
                else current_tag["status"]
            )

            duplicate_tag = self._admin_repository.get_tag_by_name(connection, next_name)
            if duplicate_tag is not None and duplicate_tag["tag_id"] != tag_id:
                raise ValidationError("Tag name already exists.")

            if (
                current_tag["tag_name"] == next_name
                and current_tag["description"] == next_description
                and current_tag["status"] == next_status
            ):
                raise ValidationError("No tag fields changed.")

            updated_count = self._admin_repository.update_tag(
                connection,
                tag_id=tag_id,
                tag_name=next_name,
                description=next_description,
                status=next_status,
            )
            if updated_count == 0:
                raise NotFoundError(f"Tag {tag_id} could not be updated.")

            self._log_repository.create_operation_log(
                connection,
                user_id=admin_user_id,
                op_type="ADMIN_UPDATE_TAG",
                op_content=(
                    f"tag_id={tag_id}, "
                    f"name={current_tag['tag_name']}->{next_name}, "
                    f"status={current_tag['status']}->{next_status}"
                )[:200],
            )
            connection.commit()

            refreshed_tag = self._admin_repository.get_tag_context(connection, tag_id)
            assert refreshed_tag is not None

        return AdminTagMutationResponse(
            tag_id=refreshed_tag["tag_id"],
            tag_name=refreshed_tag["tag_name"],
            source=refreshed_tag["source"],
            status=refreshed_tag["status"],
            description=refreshed_tag["description"],
            message="Tag updated successfully.",
        )

    def list_login_logs(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        user_id: int | None = None,
        result: str | None = None,
    ) -> AdminLoginLogListResponse:
        if page <= 0:
            raise ValidationError("page must be greater than 0.")
        if page_size <= 0 or page_size > 100:
            raise ValidationError("page_size must be between 1 and 100.")
        if user_id is not None and user_id <= 0:
            raise ValidationError("user_id must be greater than 0.")

        normalized_result = self._normalize_enum(result)
        if normalized_result is not None and normalized_result not in self.VALID_LOGIN_RESULTS:
            raise ValidationError("result must be SUCCESS, FAILURE, or LOCKED.")

        with get_connection() as connection:
            items = self._admin_repository.list_login_logs(
                connection,
                page=page,
                page_size=page_size,
                user_id=user_id,
                result=normalized_result,
            )
            total = self._admin_repository.count_login_logs(
                connection,
                user_id=user_id,
                result=normalized_result,
            )

        return AdminLoginLogListResponse(
            items=items,
            page=page,
            page_size=page_size,
            total=total,
        )

    def list_operation_logs(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        user_id: int | None = None,
        op_type: str | None = None,
    ) -> AdminOperationLogListResponse:
        if page <= 0:
            raise ValidationError("page must be greater than 0.")
        if page_size <= 0 or page_size > 100:
            raise ValidationError("page_size must be between 1 and 100.")
        if user_id is not None and user_id <= 0:
            raise ValidationError("user_id must be greater than 0.")

        normalized_op_type = self._normalize_enum(op_type)

        with get_connection() as connection:
            items = self._admin_repository.list_operation_logs(
                connection,
                page=page,
                page_size=page_size,
                user_id=user_id,
                op_type=normalized_op_type,
            )
            total = self._admin_repository.count_operation_logs(
                connection,
                user_id=user_id,
                op_type=normalized_op_type,
            )

        return AdminOperationLogListResponse(
            items=items,
            page=page,
            page_size=page_size,
            total=total,
        )

    def update_user_status(
        self,
        *,
        admin_user_id: int,
        target_user_id: int,
        status: str,
    ) -> AdminUserMutationResponse:
        normalized_status = self._require_user_status(status)

        with get_connection() as connection:
            target_user = self._admin_repository.get_user_context(connection, target_user_id)
            if target_user is None:
                raise NotFoundError(f"User {target_user_id} was not found.")

            if target_user["status"] == normalized_status:
                raise ValidationError("User status is already set to the requested value.")

            active_admin_count = self._admin_repository.count_active_admin_users(connection)
            if target_user_id == admin_user_id and normalized_status != "ACTIVE":
                raise ValidationError("An admin cannot deactivate their own current account.")
            if (
                target_user["role"] == "ADMIN"
                and target_user["status"] == "ACTIVE"
                and active_admin_count <= 1
                and normalized_status != "ACTIVE"
            ):
                raise ValidationError("The last ADMIN account must remain ACTIVE.")

            updated_count = self._admin_repository.update_user_status(
                connection,
                user_id=target_user_id,
                status=normalized_status,
            )
            if updated_count == 0:
                raise NotFoundError(f"User {target_user_id} could not be updated.")

            self._log_repository.create_operation_log(
                connection,
                user_id=admin_user_id,
                op_type="ADMIN_UPDATE_USER_STATUS",
                op_content=(
                    f"user_id={target_user_id}, username={target_user['username']}, "
                    f"from={target_user['status']}, to={normalized_status}"
                ),
            )
            connection.commit()

            refreshed_user = self._admin_repository.get_user_context(connection, target_user_id)
            assert refreshed_user is not None

        return AdminUserMutationResponse(
            user_id=refreshed_user["user_id"],
            username=refreshed_user["username"],
            role=refreshed_user["role"],
            status=refreshed_user["status"],
            message="User status updated successfully.",
        )

    def update_user_role(
        self,
        *,
        admin_user_id: int,
        target_user_id: int,
        role: str,
    ) -> AdminUserMutationResponse:
        normalized_role = self._require_user_role(role)

        with get_connection() as connection:
            target_user = self._admin_repository.get_user_context(connection, target_user_id)
            if target_user is None:
                raise NotFoundError(f"User {target_user_id} was not found.")

            if target_user["role"] == normalized_role:
                raise ValidationError("User role is already set to the requested value.")

            active_admin_count = self._admin_repository.count_active_admin_users(connection)
            if target_user_id == admin_user_id and normalized_role != "ADMIN":
                raise ValidationError("You cannot remove your own ADMIN role.")
            if (
                target_user["role"] == "ADMIN"
                and target_user["status"] == "ACTIVE"
                and active_admin_count <= 1
                and normalized_role != "ADMIN"
            ):
                raise ValidationError("The last ADMIN account cannot be demoted.")

            updated_count = self._admin_repository.update_user_role(
                connection,
                user_id=target_user_id,
                role=normalized_role,
            )
            if updated_count == 0:
                raise NotFoundError(f"User {target_user_id} could not be updated.")

            self._log_repository.create_operation_log(
                connection,
                user_id=admin_user_id,
                op_type="ADMIN_UPDATE_USER_ROLE",
                op_content=(
                    f"user_id={target_user_id}, username={target_user['username']}, "
                    f"from={target_user['role']}, to={normalized_role}"
                ),
            )
            connection.commit()

            refreshed_user = self._admin_repository.get_user_context(connection, target_user_id)
            assert refreshed_user is not None

        return AdminUserMutationResponse(
            user_id=refreshed_user["user_id"],
            username=refreshed_user["username"],
            role=refreshed_user["role"],
            status=refreshed_user["status"],
            message="User role updated successfully.",
        )

    def update_question_status(
        self,
        *,
        admin_user_id: int,
        question_id: int,
        status: str,
    ) -> AdminQuestionStatusResponse:
        normalized_status = self._require_question_status(status)

        with get_connection() as connection:
            question = self._admin_repository.get_question_context(connection, question_id)
            if question is None:
                raise NotFoundError(f"Question {question_id} was not found.")
            if question["status"] == normalized_status:
                raise ValidationError("Question status is already set to the requested value.")

            updated_count = self._admin_repository.update_question_status(
                connection,
                question_id=question_id,
                status=normalized_status,
            )
            if updated_count == 0:
                raise NotFoundError(f"Question {question_id} could not be updated.")

            self._log_repository.create_operation_log(
                connection,
                user_id=admin_user_id,
                op_type="ADMIN_UPDATE_QUESTION_STATUS",
                op_content=(
                    f"question_id={question_id}, title={question['title']}, "
                    f"from={question['status']}, to={normalized_status}"
                ),
            )
            connection.commit()

        return AdminQuestionStatusResponse(
            question_id=question_id,
            status=normalized_status,
            message="Question status updated successfully.",
        )

    def update_comment_status(
        self,
        *,
        admin_user_id: int,
        comment_id: int,
        status: str,
    ) -> AdminCommentStatusResponse:
        normalized_status = self._require_comment_status(status)

        with get_connection() as connection:
            comment = self._admin_repository.get_comment_context(connection, comment_id)
            if comment is None:
                raise NotFoundError(f"Comment {comment_id} was not found.")
            if comment["status"] == normalized_status:
                raise ValidationError("Comment status is already set to the requested value.")

            updated_count = self._admin_repository.update_comment_status(
                connection,
                comment_id=comment_id,
                status=normalized_status,
            )
            if updated_count == 0:
                raise NotFoundError(f"Comment {comment_id} could not be updated.")

            self._log_repository.create_operation_log(
                connection,
                user_id=admin_user_id,
                op_type="ADMIN_UPDATE_COMMENT_STATUS",
                op_content=(
                    f"comment_id={comment_id}, answer_id={comment['answer_id']}, "
                    f"from={comment['status']}, to={normalized_status}"
                ),
            )
            connection.commit()

        return AdminCommentStatusResponse(
            comment_id=comment_id,
            status=normalized_status,
            message="Comment status updated successfully.",
        )

    @staticmethod
    def _normalize_enum(value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip().upper()
        return normalized or None

    def _require_user_status(self, value: str) -> str:
        normalized = self._normalize_enum(value)
        if normalized not in self.VALID_USER_STATUSES:
            raise ValidationError("status must be ACTIVE, INACTIVE, LOCKED, or DISABLED.")
        return normalized

    def _require_category_name(self, value: str | None) -> str:
        if value is None:
            raise ValidationError("category_name is required.")
        normalized = value.strip()
        if not normalized:
            raise ValidationError("category_name must not be blank.")
        if len(normalized) > 50:
            raise ValidationError("category_name must be at most 50 characters.")
        return normalized

    def _require_category_status(self, value: str | None) -> str:
        normalized = self._normalize_enum(value)
        if normalized not in self.VALID_CATEGORY_STATUSES:
            raise ValidationError("status must be ACTIVE or INACTIVE.")
        return normalized

    def _require_tag_name(self, value: str | None) -> str:
        if value is None:
            raise ValidationError("tag_name is required.")
        normalized = value.strip().lstrip("#")
        normalized = " ".join(normalized.split())
        if not normalized:
            raise ValidationError("tag_name must not be blank.")
        if len(normalized) > 50:
            raise ValidationError("tag_name must be at most 50 characters.")
        return normalized.lower().replace(" ", "-")

    def _require_tag_status(self, value: str | None) -> str:
        normalized = self._normalize_enum(value)
        if normalized not in self.VALID_TAG_STATUSES:
            raise ValidationError("status must be ACTIVE, PENDING, or DISABLED.")
        return normalized

    @staticmethod
    def _normalize_description(value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None

    @staticmethod
    def _normalize_keyword(value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip().lower()
        return normalized or None

    def _require_user_role(self, value: str) -> str:
        normalized = self._normalize_enum(value)
        if normalized not in self.VALID_USER_ROLES:
            raise ValidationError("role must be USER or ADMIN.")
        return normalized

    def _require_question_status(self, value: str) -> str:
        normalized = self._normalize_enum(value)
        if normalized not in self.VALID_QUESTION_STATUSES:
            raise ValidationError("status must be OPEN, RESOLVED, CLOSED, or ARCHIVED.")
        return normalized

    def _require_comment_status(self, value: str) -> str:
        normalized = self._normalize_enum(value)
        if normalized not in self.VALID_COMMENT_STATUSES:
            raise ValidationError("status must be ACTIVE or HIDDEN.")
        return normalized
