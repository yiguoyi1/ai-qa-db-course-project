from typing import Any

import oracledb


def _normalize_returning_value(value: Any) -> int:
    if isinstance(value, list):
        value = value[0]
    return int(value)


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
                a.model_name,
                a.confidence_score,
                a.like_count,
                a.dislike_count,
                a.avg_rating,
                u.username,
                u.nickname
            FROM answers a
            LEFT JOIN users u
              ON u.user_id = a.user_id
            WHERE a.question_id = :question_id
            ORDER BY
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
                    "content": row[5].read() if hasattr(row[5], "read") else row[5],
                    "generate_time": row[6],
                    "model_name": row[7],
                    "confidence_score": float(row[8]) if row[8] is not None else None,
                    "like_count": int(row[9]),
                    "dislike_count": int(row[10]),
                    "avg_rating": float(row[11]) if row[11] is not None else None,
                    "author_username": row[12],
                    "author_nickname": row[13],
                }
            )

        return answers
