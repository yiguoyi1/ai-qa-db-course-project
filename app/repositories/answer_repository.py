from typing import Any

import oracledb


def _normalize_returning_value(value: Any) -> int:
    if isinstance(value, list):
        value = value[0]
    return int(value)


def _read_lob(value: Any) -> str:
    return value.read() if hasattr(value, "read") else value


class AnswerRepository:
    def create_ai_answer(
        self,
        connection: oracledb.Connection,
        question_id: int,
        provider_name: str,
        content: str,
        model_name: str,
    ) -> int:
        cursor = connection.cursor()
        answer_id_var = cursor.var(oracledb.NUMBER)

        cursor.execute(
            """
            INSERT INTO answers (
                question_id,
                answer_type,
                provider_name,
                content,
                model_name
            ) VALUES (
                :question_id,
                'AI',
                :provider_name,
                :content,
                :model_name
            )
            RETURNING answer_id INTO :answer_id
            """,
            {
                "question_id": question_id,
                "provider_name": provider_name,
                "content": content,
                "model_name": model_name,
                "answer_id": answer_id_var,
            },
        )

        return _normalize_returning_value(answer_id_var.getvalue())

    def create_manual_answer(
        self,
        connection: oracledb.Connection,
        question_id: int,
        user_id: int,
        content: str,
        confidence_score: float | None = None,
    ) -> int:
        cursor = connection.cursor()
        answer_id_var = cursor.var(oracledb.NUMBER)

        cursor.execute(
            """
            INSERT INTO answers (
                question_id,
                user_id,
                answer_type,
                content,
                confidence_score
            ) VALUES (
                :question_id,
                :user_id,
                'MANUAL',
                :content,
                :confidence_score
            )
            RETURNING answer_id INTO :answer_id
            """,
            {
                "question_id": question_id,
                "user_id": user_id,
                "content": content,
                "confidence_score": confidence_score,
                "answer_id": answer_id_var,
            },
        )

        return _normalize_returning_value(answer_id_var.getvalue())

    def list_answers_by_question(
        self,
        connection: oracledb.Connection,
        question_id: int,
    ) -> list[dict[str, Any]]:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT
                a.answer_id,
                a.question_id,
                a.user_id,
                a.answer_type,
                a.provider_name,
                a.content,
                a.generate_time,
                a.status,
                a.delete_time,
                a.model_name,
                a.confidence_score,
                a.like_count,
                a.dislike_count,
                a.avg_rating,
                u.username,
                u.nickname,
                m.public_url,
                CASE
                    WHEN q.accepted_answer_id = a.answer_id THEN 1
                    ELSE 0
                END AS is_accepted
            FROM answers a
            JOIN questions q
              ON q.question_id = a.question_id
            LEFT JOIN users u
              ON u.user_id = a.user_id
            LEFT JOIN media_assets m
              ON m.media_id = u.avatar_media_id
             AND m.status = 'ACTIVE'
            WHERE a.question_id = :question_id
              AND a.status = 'ACTIVE'
            ORDER BY
                CASE
                    WHEN q.accepted_answer_id = a.answer_id THEN 0
                    ELSE 1
                END,
                CASE a.answer_type
                    WHEN 'MANUAL' THEN 0
                    WHEN 'AI' THEN 1
                    ELSE 2
                END,
                a.like_count DESC,
                a.avg_rating DESC NULLS LAST,
                a.generate_time DESC,
                a.answer_id DESC
            """,
            {"question_id": question_id},
        )

        answers: list[dict[str, Any]] = []
        for row in cursor.fetchall():
            answers.append(
                {
                    "answer_id": int(row[0]),
                    "question_id": int(row[1]),
                    "user_id": int(row[2]) if row[2] is not None else None,
                    "answer_type": row[3],
                    "provider_name": row[4],
                    "content": _read_lob(row[5]),
                    "generate_time": row[6],
                    "status": row[7],
                    "delete_time": row[8],
                    "model_name": row[9],
                    "confidence_score": float(row[10]) if row[10] is not None else None,
                    "like_count": int(row[11]),
                    "dislike_count": int(row[12]),
                    "avg_rating": float(row[13]) if row[13] is not None else None,
                    "author_username": row[14],
                    "author_nickname": row[15],
                    "author_avatar_url": row[16],
                    "is_accepted": bool(row[17]),
                }
            )

        return answers

    def get_answer_by_id(
        self,
        connection: oracledb.Connection,
        answer_id: int,
    ) -> dict[str, Any] | None:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT
                answer_id,
                question_id,
                user_id,
                answer_type,
                provider_name,
                content,
                generate_time,
                status,
                delete_time,
                model_name,
                confidence_score,
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
            "answer_id": int(row[0]),
            "question_id": int(row[1]),
            "user_id": int(row[2]) if row[2] is not None else None,
            "answer_type": row[3],
            "provider_name": row[4],
            "content": _read_lob(row[5]),
            "generate_time": row[6],
            "status": row[7],
            "delete_time": row[8],
            "model_name": row[9],
            "confidence_score": float(row[10]) if row[10] is not None else None,
            "like_count": int(row[11]),
            "dislike_count": int(row[12]),
            "avg_rating": float(row[13]) if row[13] is not None else None,
        }

    def get_answer_delete_context(
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
                a.user_id,
                a.answer_type,
                a.status,
                q.title,
                q.status AS question_status,
                q.accepted_answer_id
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
            "user_id": int(row[2]) if row[2] is not None else None,
            "answer_type": row[3],
            "status": row[4],
            "question_title": row[5],
            "question_status": row[6],
            "accepted_answer_id": int(row[7]) if row[7] is not None else None,
        }

    def soft_delete_answer(
        self,
        connection: oracledb.Connection,
        *,
        answer_id: int,
    ) -> int:
        cursor = connection.cursor()
        cursor.execute(
            """
            UPDATE answers
            SET status = 'DELETED',
                delete_time = SYSDATE
            WHERE answer_id = :answer_id
              AND status <> 'DELETED'
            """,
            {"answer_id": answer_id},
        )
        return int(cursor.rowcount or 0)

    def sync_question_answer_count(
        self,
        connection: oracledb.Connection,
        *,
        question_id: int,
    ) -> None:
        cursor = connection.cursor()
        cursor.execute(
            """
            UPDATE questions q
            SET answer_count = (
                SELECT COUNT(*)
                FROM answers a
                WHERE a.question_id = q.question_id
                  AND a.status = 'ACTIVE'
            )
            WHERE q.question_id = :question_id
            """,
            {"question_id": question_id},
        )

    def get_answer_context(
        self,
        connection: oracledb.Connection,
        answer_id: int,
    ) -> dict[str, Any] | None:
        answer = self.get_answer_by_id(connection, answer_id)
        if answer is None:
            return None

        return {
            "answer_id": answer["answer_id"],
            "question_id": answer["question_id"],
            "answer_type": answer["answer_type"],
            "status": answer["status"],
        }
