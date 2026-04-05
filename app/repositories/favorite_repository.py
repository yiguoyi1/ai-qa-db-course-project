from typing import Any

import oracledb


def _normalize_returning_value(value: Any) -> int:
    if isinstance(value, list):
        value = value[0]
    return int(value)


class FavoriteRepository:
    def create_favorite(
        self,
        connection: oracledb.Connection,
        *,
        question_id: int,
        user_id: int,
    ) -> int:
        cursor = connection.cursor()
        favorite_id_var = cursor.var(oracledb.NUMBER)

        cursor.execute(
            """
            INSERT INTO favorites (
                user_id,
                question_id
            ) VALUES (
                :user_id,
                :question_id
            )
            RETURNING favorite_id INTO :favorite_id
            """,
            {
                "user_id": user_id,
                "question_id": question_id,
                "favorite_id": favorite_id_var,
            },
        )

        return _normalize_returning_value(favorite_id_var.getvalue())

    def get_favorite_record(
        self,
        connection: oracledb.Connection,
        favorite_id: int,
    ) -> dict[str, Any] | None:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT
                favorite_id,
                question_id,
                user_id,
                favorite_time
            FROM favorites
            WHERE favorite_id = :favorite_id
            """,
            {"favorite_id": favorite_id},
        )
        row = cursor.fetchone()
        if row is None:
            return None

        return {
            "favorite_id": int(row[0]),
            "question_id": int(row[1]),
            "user_id": int(row[2]),
            "favorite_time": row[3],
        }

    def delete_favorite(
        self,
        connection: oracledb.Connection,
        *,
        question_id: int,
        user_id: int,
    ) -> int:
        cursor = connection.cursor()
        cursor.execute(
            """
            DELETE FROM favorites
            WHERE question_id = :question_id
              AND user_id = :user_id
            """,
            {
                "question_id": question_id,
                "user_id": user_id,
            },
        )
        return int(cursor.rowcount or 0)

    def get_question_favorite_count(
        self,
        connection: oracledb.Connection,
        question_id: int,
    ) -> int | None:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT favorite_count
            FROM questions
            WHERE question_id = :question_id
            """,
            {"question_id": question_id},
        )
        row = cursor.fetchone()
        return int(row[0]) if row is not None else None
