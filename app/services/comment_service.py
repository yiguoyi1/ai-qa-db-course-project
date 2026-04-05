import oracledb

from app.core.errors import AppError, NotFoundError, ValidationError
from app.db.connection import get_connection
from app.repositories.comment_repository import CommentRepository
from app.schemas.comment import (
    CommentItem,
    CommentTreeResponse,
    CreateCommentRequest,
    DeleteCommentResponse,
)


class CommentService:
    def __init__(
        self,
        comment_repository: CommentRepository | None = None,
    ) -> None:
        self._comment_repository = comment_repository or CommentRepository()

    def create_comment(
        self,
        *,
        answer_id: int,
        payload: CreateCommentRequest,
    ) -> CommentItem:
        if answer_id <= 0:
            raise ValidationError("answer_id must be greater than 0.")

        content = payload.content.strip()
        if not content:
            raise ValidationError("content must not be blank.")

        with get_connection() as connection:
            answer_context = self._comment_repository.get_answer_context(connection, answer_id)
            if answer_context is None:
                raise NotFoundError(f"Answer {answer_id} was not found.")

            if answer_context["question_status"] not in {"OPEN", "RESOLVED"}:
                raise ValidationError("Only OPEN or RESOLVED questions can accept comments.")

            parent_comment_id = payload.parent_comment_id
            root_comment_id: int | None = None
            reply_to_user_id: int | None = None
            comment_level = 1

            if parent_comment_id is not None:
                parent_comment = self._comment_repository.get_comment_context(
                    connection,
                    parent_comment_id,
                )
                if parent_comment is None:
                    raise NotFoundError(
                        f"Parent comment {parent_comment_id} was not found."
                    )
                if parent_comment["answer_id"] != answer_id:
                    raise ValidationError(
                        "parent_comment_id does not belong to the specified answer."
                    )
                if parent_comment["status"] != "ACTIVE":
                    raise ValidationError("Replies can only target ACTIVE comments.")

                root_comment_id = (
                    parent_comment["root_comment_id"] or parent_comment["comment_id"]
                )
                reply_to_user_id = parent_comment["user_id"]
                comment_level = parent_comment["comment_level"] + 1

            try:
                comment_id = self._comment_repository.create_comment(
                    connection=connection,
                    answer_id=answer_id,
                    user_id=payload.user_id,
                    parent_comment_id=parent_comment_id,
                    root_comment_id=root_comment_id,
                    reply_to_user_id=reply_to_user_id,
                    content=content,
                    comment_level=comment_level,
                )

                if parent_comment_id is None:
                    self._comment_repository.set_root_comment_id(
                        connection,
                        comment_id=comment_id,
                        root_comment_id=comment_id,
                    )
                else:
                    self._comment_repository.increment_reply_count(
                        connection,
                        comment_id=parent_comment_id,
                    )

                connection.commit()
            except oracledb.DatabaseError as exc:
                connection.rollback()
                raise self._translate_database_error(exc) from exc
            except Exception:
                connection.rollback()
                raise

            comment = self._comment_repository.get_comment_detail(connection, comment_id)
            if comment is None:
                raise NotFoundError("Comment was created but could not be reloaded.")

        return CommentItem(**comment)

    def delete_comment(
        self,
        *,
        comment_id: int,
        user_id: int,
    ) -> DeleteCommentResponse:
        if comment_id <= 0:
            raise ValidationError("comment_id must be greater than 0.")
        if user_id <= 0:
            raise ValidationError("user_id must be greater than 0.")

        with get_connection() as connection:
            comment = self._comment_repository.get_comment_context(connection, comment_id)
            if comment is None:
                raise NotFoundError(f"Comment {comment_id} was not found.")
            if comment["user_id"] != user_id:
                raise ValidationError("Only the comment author can delete the comment.")
            if comment["status"] == "DELETED":
                raise ValidationError("Comment has already been deleted.")

            try:
                deleted_count = self._comment_repository.soft_delete_comment(
                    connection,
                    comment_id=comment_id,
                )
                connection.commit()
            except oracledb.DatabaseError as exc:
                connection.rollback()
                raise self._translate_database_error(exc) from exc
            except Exception:
                connection.rollback()
                raise

            if deleted_count == 0:
                raise NotFoundError(f"Comment {comment_id} could not be deleted.")

        return DeleteCommentResponse(
            comment_id=comment_id,
            user_id=user_id,
            status="DELETED",
            deleted=True,
        )

    def list_comments(
        self,
        *,
        answer_id: int,
    ) -> CommentTreeResponse:
        if answer_id <= 0:
            raise ValidationError("answer_id must be greater than 0.")

        with get_connection() as connection:
            answer_context = self._comment_repository.get_answer_context(connection, answer_id)
            if answer_context is None:
                raise NotFoundError(f"Answer {answer_id} was not found.")

            flat_comments = self._comment_repository.list_comments_by_answer(connection, answer_id)

        for comment in flat_comments:
            if comment["status"] == "DELETED":
                comment["content"] = self._deleted_placeholder(
                    is_reply=comment["parent_comment_id"] is not None
                )

        nodes = [CommentItem(**comment) for comment in flat_comments]
        node_by_id = {node.comment_id: node for node in nodes}
        roots: list[CommentItem] = []

        for node in nodes:
            if node.parent_comment_id is None:
                roots.append(node)
                continue

            parent = node_by_id.get(node.parent_comment_id)
            if parent is None:
                roots.append(node)
                continue

            parent.children.append(node)

        return CommentTreeResponse(answer_id=answer_id, total=len(nodes), items=roots)

    @staticmethod
    def _translate_database_error(exc: oracledb.DatabaseError) -> AppError:
        details = exc.args[0] if exc.args else exc
        message = getattr(details, "message", str(details))

        if "ORA-02291" in message:
            return ValidationError(
                "answer_id, user_id, or parent comment contains an invalid reference."
            )
        if "ORA-02290" in message:
            return ValidationError("Comment data violates a database constraint.")

        return AppError(f"Database operation failed: {message}", status_code=500)

    @staticmethod
    def _deleted_placeholder(*, is_reply: bool) -> str:
        return "原回复已删除" if is_reply else "原评论已删除"
