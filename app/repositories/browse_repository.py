from typing import Any

import oracledb


def _normalize_returning_value(value: Any) -> int:
    if isinstance(value, list):
        value = value[0]
    return int(value)


class BrowseRepository:
    def create_browse_record(
        self,
        connection: oracledb.Connection,
        *,
        question_id: int,
        user_id: int,
        duration: int,
        click_depth: int,
    ) -> int:
        cursor = connection.cursor()
        history_id_var = cursor.var(oracledb.NUMBER)

        cursor.execute(
            """
            INSERT INTO browse_history (
                user_id,
                question_id,
                duration,
                click_depth
            ) VALUES (
                :user_id,
                :question_id,
                :duration,
                :click_depth
            )
            RETURNING history_id INTO :history_id
            """,
            {
                "user_id": user_id,
                "question_id": question_id,
                "duration": duration,
                "click_depth": click_depth,
                "history_id": history_id_var,
            },
        )

        return _normalize_returning_value(history_id_var.getvalue())

    def get_browse_record(
        self,
        connection: oracledb.Connection,
        history_id: int,
    ) -> dict[str, Any] | None:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT
                history_id,
                question_id,
                user_id,
                browse_time,
                duration,
                click_depth
            FROM browse_history
            WHERE history_id = :history_id
            """,
            {"history_id": history_id},
        )
        row = cursor.fetchone()
        if row is None:
            return None

        return {
            "history_id": int(row[0]),
            "question_id": int(row[1]),
            "user_id": int(row[2]),
            "browse_time": row[3],
            "duration": int(row[4]),
            "click_depth": int(row[5]),
        }

    def get_question_view_count(
        self,
        connection: oracledb.Connection,
        question_id: int,
    ) -> int | None:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT view_count
            FROM questions
            WHERE question_id = :question_id
            """,
            {"question_id": question_id},
        )
        row = cursor.fetchone()
        return int(row[0]) if row is not None else None
