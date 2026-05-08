from typing import Any

import oracledb


def _normalize_returning_value(value: Any) -> int:
    if isinstance(value, list):
        value = value[0]
    return int(value)


def _read_lob(value: Any) -> str:
    return value.read() if hasattr(value, "read") else value


def _serialize_comment_row(row: tuple[Any, ...]) -> dict[str, Any]:
    return {
        "comment_id": int(row[0]),
        "answer_id": int(row[1]),
        "user_id": int(row[2]),
        "parent_comment_id": int(row[3]) if row[3] is not None else None,
        "root_comment_id": int(row[4]) if row[4] is not None else None,
        "reply_to_user_id": int(row[5]) if row[5] is not None else None,
        "comment_level": int(row[6]),
        "status": row[7],
        "content": _read_lob(row[8]),
        "reply_count": int(row[9]),
        "create_time": row[10],
        "update_time": row[11],
        "author_username": row[12],
        "author_nickname": row[13],
        "author_avatar_url": row[14],
        "reply_to_username": row[15],
        "reply_to_nickname": row[16],
    }


class CommentRepository:
    def get_answer_context(
        self,
        connection: oracledb.Connection,
        answer_id: int,
    ) -> dict[str, Any] | None:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT
                a.answer_id,
                a.question_id,
                a.status,
                q.status
            FROM answers a
            JOIN questions q
              ON q.question_id = a.question_id
            WHERE a.answer_id = :answer_id
            """,
            {"answer_id": answer_id},
        )
        row = cursor.fetchone()
        if row is None:
            return None

        return {
            "answer_id": int(row[0]),
            "question_id": int(row[1]),
            "answer_status": row[2],
            "question_status": row[3],
        }

    def get_comment_context(
        self,
        connection: oracledb.Connection,
        comment_id: int,
    ) -> dict[str, Any] | None:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT
                comment_id,
                answer_id,
                user_id,
                parent_comment_id,
                root_comment_id,
                comment_level,
                status
            FROM answer_comments
            WHERE comment_id = :comment_id
            """,
            {"comment_id": comment_id},
        )
        row = cursor.fetchone()
        if row is None:
            return None

        return {
            "comment_id": int(row[0]),
            "answer_id": int(row[1]),
            "user_id": int(row[2]),
            "parent_comment_id": int(row[3]) if row[3] is not None else None,
            "root_comment_id": int(row[4]) if row[4] is not None else None,
            "comment_level": int(row[5]),
            "status": row[6],
        }

    def soft_delete_comment(
        self,
        connection: oracledb.Connection,
        *,
        comment_id: int,
    ) -> int:
        cursor = connection.cursor()
        cursor.execute(
            """
            UPDATE answer_comments
            SET status = 'DELETED',
                update_time = SYSDATE,
                delete_time = SYSDATE
            WHERE comment_id = :comment_id
              AND status <> 'DELETED'
            """,
            {"comment_id": comment_id},
        )
        return int(cursor.rowcount or 0)

    def create_comment(
        self,
        connection: oracledb.Connection,
        *,
        answer_id: int,
        user_id: int,
        parent_comment_id: int | None,
        root_comment_id: int | None,
        reply_to_user_id: int | None,
        content: str,
        comment_level: int,
    ) -> int:
        cursor = connection.cursor()
        comment_id_var = cursor.var(oracledb.NUMBER)

        cursor.execute(
            """
            INSERT INTO answer_comments (
                answer_id,
                user_id,
                parent_comment_id,
                root_comment_id,
                reply_to_user_id,
                content,
                comment_level,
                status,
                update_time
            ) VALUES (
                :answer_id,
                :user_id,
                :parent_comment_id,
                :root_comment_id,
                :reply_to_user_id,
                :content,
                :comment_level,
                'ACTIVE',
                SYSDATE
            )
            RETURNING comment_id INTO :comment_id
            """,
            {
                "answer_id": answer_id,
                "user_id": user_id,
                "parent_comment_id": parent_comment_id,
                "root_comment_id": root_comment_id,
                "reply_to_user_id": reply_to_user_id,
                "content": content,
                "comment_level": comment_level,
                "comment_id": comment_id_var,
            },
        )

        return _normalize_returning_value(comment_id_var.getvalue())

    def set_root_comment_id(
        self,
        connection: oracledb.Connection,
        *,
        comment_id: int,
        root_comment_id: int,
    ) -> None:
        cursor = connection.cursor()
        cursor.execute(
            """
            UPDATE answer_comments
            SET root_comment_id = :root_comment_id,
                update_time = SYSDATE
            WHERE comment_id = :comment_id
            """,
            {
                "comment_id": comment_id,
                "root_comment_id": root_comment_id,
            },
        )

    def increment_reply_count(
        self,
        connection: oracledb.Connection,
        *,
        comment_id: int,
    ) -> None:
        cursor = connection.cursor()
        cursor.execute(
            """
            UPDATE answer_comments
            SET reply_count = reply_count + 1
            WHERE comment_id = :comment_id
            """,
            {"comment_id": comment_id},
        )

    def get_comment_detail(
        self,
        connection: oracledb.Connection,
        comment_id: int,
    ) -> dict[str, Any] | None:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT
                ac.comment_id,
                ac.answer_id,
                ac.user_id,
                ac.parent_comment_id,
                ac.root_comment_id,
                ac.reply_to_user_id,
                ac.comment_level,
                ac.status,
                ac.content,
                ac.reply_count,
                ac.create_time,
                ac.update_time,
                author.username,
                author.nickname,
                author_avatar.public_url,
                reply_user.username,
                reply_user.nickname
            FROM answer_comments ac
            JOIN users author
              ON author.user_id = ac.user_id
            LEFT JOIN media_assets author_avatar
              ON author_avatar.media_id = author.avatar_media_id
             AND author_avatar.status = 'ACTIVE'
            LEFT JOIN users reply_user
              ON reply_user.user_id = ac.reply_to_user_id
            WHERE ac.comment_id = :comment_id
            """,
            {"comment_id": comment_id},
        )
        row = cursor.fetchone()
        if row is None:
            return None

        return _serialize_comment_row(row)

    def list_comments_by_answer(
        self,
        connection: oracledb.Connection,
        answer_id: int,
    ) -> list[dict[str, Any]]:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT
                ac.comment_id,
                ac.answer_id,
                ac.user_id,
                ac.parent_comment_id,
                ac.root_comment_id,
                ac.reply_to_user_id,
                ac.comment_level,
                ac.status,
                ac.content,
                ac.reply_count,
                ac.create_time,
                ac.update_time,
                author.username,
                author.nickname,
                author_avatar.public_url,
                reply_user.username,
                reply_user.nickname
            FROM answer_comments ac
            JOIN users author
              ON author.user_id = ac.user_id
            LEFT JOIN media_assets author_avatar
              ON author_avatar.media_id = author.avatar_media_id
             AND author_avatar.status = 'ACTIVE'
            LEFT JOIN users reply_user
              ON reply_user.user_id = ac.reply_to_user_id
            WHERE ac.answer_id = :answer_id
            ORDER BY
                NVL(ac.root_comment_id, ac.comment_id),
                ac.comment_level,
                ac.create_time,
                ac.comment_id
            """,
            {"answer_id": answer_id},
        )

        return [_serialize_comment_row(row) for row in cursor.fetchall()]
