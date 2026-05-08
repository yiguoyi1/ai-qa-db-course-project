from typing import Any

import oracledb


def _normalize_returning_value(value: Any) -> int:
    if isinstance(value, list):
        value = value[0]
    return int(value)


def _read_lob(value: Any) -> str:
    return value.read() if hasattr(value, "read") else value


class ChatRepository:
    def create_session(
        self,
        connection: oracledb.Connection,
        *,
        user_id: int,
        question_id: int,
        seed_answer_id: int,
    ) -> int:
        cursor = connection.cursor()
        session_id_var = cursor.var(oracledb.NUMBER)
        cursor.execute(
            """
            INSERT INTO chat_session (
                user_id,
                question_id,
                seed_answer_id,
                status
            ) VALUES (
                :user_id,
                :question_id,
                :seed_answer_id,
                'OPEN'
            )
            RETURNING session_id INTO :session_id
            """,
            {
                "user_id": user_id,
                "question_id": question_id,
                "seed_answer_id": seed_answer_id,
                "session_id": session_id_var,
            },
        )
        return _normalize_returning_value(session_id_var.getvalue())

    def create_message(
        self,
        connection: oracledb.Connection,
        *,
        session_id: int,
        sender_type: str,
        content: str,
        model_name: str | None = None,
    ) -> int:
        cursor = connection.cursor()
        message_id_var = cursor.var(oracledb.NUMBER)
        cursor.execute(
            """
            INSERT INTO chat_message (
                session_id,
                sender_type,
                content,
                model_name
            ) VALUES (
                :session_id,
                :sender_type,
                :content,
                :model_name
            )
            RETURNING message_id INTO :message_id
            """,
            {
                "session_id": session_id,
                "sender_type": sender_type,
                "content": content,
                "model_name": model_name,
                "message_id": message_id_var,
            },
        )
        return _normalize_returning_value(message_id_var.getvalue())

    def get_session_by_id(
        self,
        connection: oracledb.Connection,
        session_id: int,
    ) -> dict[str, Any] | None:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT
                cs.session_id,
                cs.user_id,
                u.username,
                u.nickname,
                cs.question_id,
                cs.seed_answer_id,
                cs.status,
                cs.start_time,
                cs.end_time,
                COUNT(cm.message_id) AS message_count,
                MAX(cm.send_time) AS last_message_time
            FROM chat_session cs
            JOIN users u
              ON u.user_id = cs.user_id
            LEFT JOIN chat_message cm
              ON cm.session_id = cs.session_id
            WHERE cs.session_id = :session_id
            GROUP BY
                cs.session_id,
                cs.user_id,
                u.username,
                u.nickname,
                cs.question_id,
                cs.seed_answer_id,
                cs.status,
                cs.start_time,
                cs.end_time
            """,
            {"session_id": session_id},
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return {
            "session_id": int(row[0]),
            "user_id": int(row[1]),
            "username": row[2],
            "nickname": row[3],
            "question_id": int(row[4]),
            "seed_answer_id": int(row[5]),
            "status": row[6],
            "start_time": row[7],
            "end_time": row[8],
            "message_count": int(row[9] or 0),
            "last_message_time": row[10],
        }

    def list_sessions_by_anchor(
        self,
        connection: oracledb.Connection,
        *,
        question_id: int,
        seed_answer_id: int,
        user_id: int,
    ) -> list[dict[str, Any]]:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT
                cs.session_id,
                cs.user_id,
                u.username,
                u.nickname,
                cs.question_id,
                cs.seed_answer_id,
                cs.status,
                cs.start_time,
                cs.end_time,
                COUNT(cm.message_id) AS message_count,
                MAX(cm.send_time) AS last_message_time
            FROM chat_session cs
            JOIN users u
              ON u.user_id = cs.user_id
            LEFT JOIN chat_message cm
              ON cm.session_id = cs.session_id
            WHERE cs.question_id = :question_id
              AND cs.seed_answer_id = :seed_answer_id
              AND cs.user_id = :user_id
            GROUP BY
                cs.session_id,
                cs.user_id,
                u.username,
                u.nickname,
                cs.question_id,
                cs.seed_answer_id,
                cs.status,
                cs.start_time,
                cs.end_time
            ORDER BY cs.start_time DESC, cs.session_id DESC
            """,
            {
                "question_id": question_id,
                "seed_answer_id": seed_answer_id,
                "user_id": user_id,
            },
        )
        return [
            {
                "session_id": int(row[0]),
                "user_id": int(row[1]),
                "username": row[2],
                "nickname": row[3],
                "question_id": int(row[4]),
                "seed_answer_id": int(row[5]),
                "status": row[6],
                "start_time": row[7],
                "end_time": row[8],
                "message_count": int(row[9] or 0),
                "last_message_time": row[10],
            }
            for row in cursor.fetchall()
        ]

    def list_messages_by_session(
        self,
        connection: oracledb.Connection,
        *,
        session_id: int,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        cursor = connection.cursor()
        sql = """
            SELECT
                message_id,
                session_id,
                sender_type,
                content,
                send_time,
                model_name
            FROM chat_message
            WHERE session_id = :session_id
            ORDER BY send_time, message_id
        """
        binds: dict[str, Any] = {"session_id": session_id}
        if limit is not None:
            sql = f"""
                SELECT * FROM (
                    SELECT
                        message_id,
                        session_id,
                        sender_type,
                        content,
                        send_time,
                        model_name
                    FROM chat_message
                    WHERE session_id = :session_id
                    ORDER BY send_time DESC, message_id DESC
                )
                WHERE ROWNUM <= :limit
                ORDER BY send_time, message_id
            """
            binds["limit"] = limit

        cursor.execute(sql, binds)
        return [
            {
                "message_id": int(row[0]),
                "session_id": int(row[1]),
                "sender_type": row[2],
                "content": _read_lob(row[3]),
                "send_time": row[4],
                "model_name": row[5],
            }
            for row in cursor.fetchall()
        ]
