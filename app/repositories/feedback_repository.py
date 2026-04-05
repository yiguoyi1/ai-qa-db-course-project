from typing import Any

import oracledb


def _normalize_returning_value(value: Any) -> int:
    if isinstance(value, list):
        value = value[0]
    return int(value)


class FeedbackRepository:
    def find_feedback_id(
        self,
        connection: oracledb.Connection,
        *,
        answer_id: int,
        user_id: int,
    ) -> int | None:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT feedback_id
            FROM answer_feedback
            WHERE answer_id = :answer_id
              AND user_id = :user_id
            """,
            {
                "answer_id": answer_id,
                "user_id": user_id,
            },
        )
        row = cursor.fetchone()
        return int(row[0]) if row is not None else None

    def create_feedback(
        self,
        connection: oracledb.Connection,
        *,
        answer_id: int,
        user_id: int,
        is_like: str,
        rating: float | None,
        comment_text: str | None,
    ) -> int:
        cursor = connection.cursor()
        feedback_id_var = cursor.var(oracledb.NUMBER)

        cursor.execute(
            """
            INSERT INTO answer_feedback (
                answer_id,
                user_id,
                is_like,
                rating,
                comment_text
            ) VALUES (
                :answer_id,
                :user_id,
                :is_like,
                :rating,
                :comment_text
            )
            RETURNING feedback_id INTO :feedback_id
            """,
            {
                "answer_id": answer_id,
                "user_id": user_id,
                "is_like": is_like,
                "rating": rating,
                "comment_text": comment_text,
                "feedback_id": feedback_id_var,
            },
        )

        return _normalize_returning_value(feedback_id_var.getvalue())

    def update_feedback(
        self,
        connection: oracledb.Connection,
        *,
        feedback_id: int,
        is_like: str,
        rating: float | None,
        comment_text: str | None,
    ) -> None:
        cursor = connection.cursor()
        cursor.execute(
            """
            UPDATE answer_feedback
            SET is_like = :is_like,
                rating = :rating,
                comment_text = :comment_text,
                feedback_time = SYSDATE
            WHERE feedback_id = :feedback_id
            """,
            {
                "feedback_id": feedback_id,
                "is_like": is_like,
                "rating": rating,
                "comment_text": comment_text,
            },
        )

    def get_feedback_record(
        self,
        connection: oracledb.Connection,
        feedback_id: int,
    ) -> dict[str, Any] | None:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT
                feedback_id,
                answer_id,
                user_id,
                is_like,
                rating,
                comment_text,
                feedback_time
            FROM answer_feedback
            WHERE feedback_id = :feedback_id
            """,
            {"feedback_id": feedback_id},
        )
        row = cursor.fetchone()
        if row is None:
            return None

        return {
            "feedback_id": int(row[0]),
            "answer_id": int(row[1]),
            "user_id": int(row[2]),
            "is_like": row[3],
            "rating": float(row[4]) if row[4] is not None else None,
            "comment_text": row[5],
            "feedback_time": row[6],
        }

    def get_answer_feedback_stats(
        self,
        connection: oracledb.Connection,
        answer_id: int,
    ) -> dict[str, Any] | None:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT
                like_count,
                dislike_count,
                avg_rating
            FROM answers
            WHERE answer_id = :answer_id
            """,
            {"answer_id": answer_id},
        )
        row = cursor.fetchone()
        if row is None:
            return None

        return {
            "like_count": int(row[0]),
            "dislike_count": int(row[1]),
            "avg_rating": float(row[2]) if row[2] is not None else None,
        }
