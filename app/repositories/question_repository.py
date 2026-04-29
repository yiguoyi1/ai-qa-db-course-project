from typing import Any

import oracledb


def _normalize_returning_value(value: Any) -> int:
    if isinstance(value, list):
        value = value[0]
    return int(value)


class QuestionRepository:
    @staticmethod
    def _attach_favorite_state(
        connection: oracledb.Connection,
        items: list[dict[str, Any]],
        *,
        question_id_getter,
        current_user_id: int | None,
    ) -> None:
        if not items:
            return

        if current_user_id is None:
            for item in items:
                item["is_favorited"] = False
            return

        question_ids = list(dict.fromkeys(question_id_getter(item) for item in items))
        binds = {"user_id": current_user_id}
        binds.update(
            {
                f"question_id_{index}": question_id
                for index, question_id in enumerate(question_ids)
            }
        )
        placeholders = ", ".join(
            f":question_id_{index}" for index in range(len(question_ids))
        )

        cursor = connection.cursor()
        cursor.execute(
            f"""
            SELECT question_id
            FROM favorites
            WHERE user_id = :user_id
              AND question_id IN ({placeholders})
            """,
            binds,
        )
        favorited_question_ids = {int(row[0]) for row in cursor.fetchall()}

        for item in items:
            item["is_favorited"] = question_id_getter(item) in favorited_question_ids

    @staticmethod
    def _build_question_filters(
        category_id: int | None,
        tag_id: int | None,
        status: str | None,
    ) -> tuple[list[str], dict[str, Any]]:
        clauses = ["1 = 1"]
        binds: dict[str, Any] = {}

        if category_id is not None:
            clauses.append("q.category_id = :category_id")
            binds["category_id"] = category_id

        if tag_id is not None:
            clauses.append(
                """
                EXISTS (
                    SELECT 1
                    FROM question_tags qt_filter
                    JOIN tags t_filter
                      ON t_filter.tag_id = qt_filter.tag_id
                     AND t_filter.status = 'ACTIVE'
                    WHERE qt_filter.question_id = q.question_id
                      AND qt_filter.tag_id = :tag_id
                )
                """
            )
            binds["tag_id"] = tag_id

        if status is not None:
            clauses.append("q.status = :status")
            binds["status"] = status
        else:
            clauses.append("q.status <> 'DELETED'")

        return clauses, binds

    def create_question(
        self,
        connection: oracledb.Connection,
        user_id: int,
        category_id: int,
        title: str,
        content: str,
    ) -> int:
        cursor = connection.cursor()
        question_id_var = cursor.var(oracledb.NUMBER)

        cursor.execute(
            """
            INSERT INTO questions (
                user_id,
                category_id,
                title,
                content,
                status
            ) VALUES (
                :user_id,
                :category_id,
                :title,
                :content,
                'OPEN'
            )
            RETURNING question_id INTO :question_id
            """,
            {
                "user_id": user_id,
                "category_id": category_id,
                "title": title,
                "content": content,
                "question_id": question_id_var,
            },
        )

        return _normalize_returning_value(question_id_var.getvalue())

    def get_first_active_category_id(
        self,
        connection: oracledb.Connection,
    ) -> int | None:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT category_id
            FROM categories
            WHERE status = 'ACTIVE'
            ORDER BY category_id
            FETCH FIRST 1 ROWS ONLY
            """
        )
        row = cursor.fetchone()
        return int(row[0]) if row is not None else None

    def add_tags(
        self,
        connection: oracledb.Connection,
        question_id: int,
        tag_ids: list[int],
        *,
        source: str = "USER_SELECTED",
        confidence_score: float | None = None,
    ) -> None:
        if not tag_ids:
            return

        deduplicated_tag_ids = list(dict.fromkeys(tag_ids))
        rows = [
            {
                "question_id": question_id,
                "tag_id": tag_id,
                "source": source,
                "confidence_score": confidence_score,
            }
            for tag_id in deduplicated_tag_ids
        ]

        cursor = connection.cursor()
        cursor.executemany(
            """
            INSERT INTO question_tags (
                question_id,
                tag_id,
                source,
                confidence_score
            ) VALUES (
                :question_id,
                :tag_id,
                :source,
                :confidence_score
            )
            """,
            rows,
        )

    def get_question_detail(
        self,
        connection: oracledb.Connection,
        question_id: int,
        current_user_id: int | None = None,
    ) -> dict[str, Any] | None:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT
                q.question_id,
                q.user_id,
                q.category_id,
                q.title,
                q.content,
                q.ask_time,
                q.status,
                q.accepted_answer_id,
                q.view_count,
                q.favorite_count,
                q.answer_count,
                u.username,
                u.nickname,
                m.public_url
            FROM questions q
            LEFT JOIN users u
              ON q.user_id = u.user_id
            LEFT JOIN media_assets m
              ON m.media_id = u.avatar_media_id
             AND m.status = 'ACTIVE'
            WHERE q.question_id = :question_id
            """,
            {"question_id": question_id},
        )
        row = cursor.fetchone()
        if row is None:
            return None

        question = {
            "question_id": int(row[0]),
            "user_id": int(row[1]),
            "category_id": int(row[2]),
            "title": row[3],
            "content": row[4].read() if hasattr(row[4], "read") else row[4],
            "ask_time": row[5],
            "status": row[6],
            "accepted_answer_id": int(row[7]) if row[7] is not None else None,
            "view_count": int(row[8]),
            "favorite_count": int(row[9]),
            "answer_count": int(row[10]),
            "username": row[11],
            "author_nickname": row[12],
            "author_avatar_url": row[13],
            "is_favorited": False,
        }

        cursor.execute(
            """
            SELECT t.tag_id, t.tag_name
            FROM question_tags qt
            JOIN tags t
              ON t.tag_id = qt.tag_id
             AND t.status = 'ACTIVE'
            WHERE qt.question_id = :question_id
            ORDER BY t.tag_name
            """,
            {"question_id": question_id},
        )
        question["tags"] = [
            {"tag_id": int(tag_row[0]), "tag_name": tag_row[1]}
            for tag_row in cursor.fetchall()
        ]
        self._attach_favorite_state(
            connection,
            [question],
            question_id_getter=lambda item: item["question_id"],
            current_user_id=current_user_id,
        )

        return question

    def get_question_acceptance_context(
        self,
        connection: oracledb.Connection,
        question_id: int,
    ) -> dict[str, Any] | None:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT
                question_id,
                user_id,
                status,
                accepted_answer_id
            FROM questions
            WHERE question_id = :question_id
            """,
            {"question_id": question_id},
        )
        row = cursor.fetchone()
        if row is None:
            return None

        return {
            "question_id": int(row[0]),
            "user_id": int(row[1]),
            "status": row[2],
            "accepted_answer_id": int(row[3]) if row[3] is not None else None,
        }

    def get_question_context(
        self,
        connection: oracledb.Connection,
        question_id: int,
    ) -> dict[str, Any] | None:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT
                question_id,
                user_id,
                title,
                status
            FROM questions
            WHERE question_id = :question_id
            """,
            {"question_id": question_id},
        )
        row = cursor.fetchone()
        if row is None:
            return None

        return {
            "question_id": int(row[0]),
            "user_id": int(row[1]),
            "title": row[2],
            "status": row[3],
        }

    def update_question_status(
        self,
        connection: oracledb.Connection,
        *,
        question_id: int,
        status: str,
    ) -> int:
        cursor = connection.cursor()
        cursor.execute(
            """
            UPDATE questions
            SET status = :status
            WHERE question_id = :question_id
            """,
            {"question_id": question_id, "status": status},
        )
        return int(cursor.rowcount or 0)

    def accept_answer(
        self,
        connection: oracledb.Connection,
        *,
        question_id: int,
        answer_id: int,
    ) -> int:
        cursor = connection.cursor()
        cursor.execute(
            """
            UPDATE questions q
            SET accepted_answer_id = :answer_id,
                status = 'RESOLVED'
            WHERE q.question_id = :question_id
              AND q.status NOT IN ('CLOSED', 'ARCHIVED', 'DELETED')
              AND EXISTS (
                  SELECT 1
                  FROM answers a
                  WHERE a.answer_id = :answer_id
                    AND a.question_id = q.question_id
                    AND a.answer_type <> 'SYSTEM'
              )
            """,
            {
                "question_id": question_id,
                "answer_id": answer_id,
            },
        )
        return int(cursor.rowcount or 0)

    def count_questions(
        self,
        connection: oracledb.Connection,
        *,
        category_id: int | None = None,
        tag_id: int | None = None,
        status: str | None = None,
    ) -> int:
        where_clauses, binds = self._build_question_filters(
            category_id=category_id,
            tag_id=tag_id,
            status=status,
        )

        cursor = connection.cursor()
        cursor.execute(
            f"""
            SELECT COUNT(*)
            FROM questions q
            WHERE {' AND '.join(where_clauses)}
            """,
            binds,
        )
        row = cursor.fetchone()
        return int(row[0]) if row is not None else 0

    def list_questions(
        self,
        connection: oracledb.Connection,
        *,
        page: int,
        page_size: int,
        category_id: int | None = None,
        tag_id: int | None = None,
        status: str | None = None,
        current_user_id: int | None = None,
    ) -> list[dict[str, Any]]:
        where_clauses, binds = self._build_question_filters(
            category_id=category_id,
            tag_id=tag_id,
            status=status,
        )
        binds.update(
            {
                "offset_rows": (page - 1) * page_size,
                "fetch_rows": page_size,
            }
        )

        cursor = connection.cursor()
        cursor.execute(
            f"""
            SELECT
                q.question_id,
                q.user_id,
                q.category_id,
                q.title,
                q.ask_time,
                q.status,
                q.view_count,
                q.favorite_count,
                q.answer_count,
                u.username,
                u.nickname,
                m.public_url
            FROM questions q
            LEFT JOIN users u
              ON q.user_id = u.user_id
            LEFT JOIN media_assets m
              ON m.media_id = u.avatar_media_id
             AND m.status = 'ACTIVE'
            WHERE {' AND '.join(where_clauses)}
            ORDER BY q.ask_time DESC, q.question_id DESC
            OFFSET :offset_rows ROWS FETCH NEXT :fetch_rows ROWS ONLY
            """,
            binds,
        )

        rows = cursor.fetchall()
        if not rows:
            return []

        questions = [
            {
                "question_id": int(row[0]),
                "user_id": int(row[1]),
                "category_id": int(row[2]),
                "title": row[3],
                "ask_time": row[4],
                "status": row[5],
                "view_count": int(row[6]),
                "favorite_count": int(row[7]),
                "answer_count": int(row[8]),
                "username": row[9],
                "author_nickname": row[10],
                "is_favorited": False,
                "author_avatar_url": row[11],
                "tags": [],
            }
            for row in rows
        ]

        question_ids = [question["question_id"] for question in questions]
        tag_binds = {
            f"question_id_{index}": question_id
            for index, question_id in enumerate(question_ids)
        }
        placeholders = ", ".join(f":question_id_{index}" for index in range(len(question_ids)))

        cursor.execute(
            f"""
            SELECT
                qt.question_id,
                t.tag_id,
                t.tag_name
            FROM question_tags qt
            JOIN tags t
              ON t.tag_id = qt.tag_id
             AND t.status = 'ACTIVE'
            WHERE qt.question_id IN ({placeholders})
            ORDER BY qt.question_id, t.tag_name
            """,
            tag_binds,
        )

        tags_by_question_id: dict[int, list[dict[str, Any]]] = {
            question_id: [] for question_id in question_ids
        }
        for row in cursor.fetchall():
            tags_by_question_id[int(row[0])].append(
                {
                    "tag_id": int(row[1]),
                    "tag_name": row[2],
                }
            )

        for question in questions:
            question["tags"] = tags_by_question_id.get(question["question_id"], [])

        self._attach_favorite_state(
            connection,
            questions,
            question_id_getter=lambda item: item["question_id"],
            current_user_id=current_user_id,
        )

        return questions
