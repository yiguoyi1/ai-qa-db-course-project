from typing import Any

import oracledb


def _normalize_returning_value(value: Any) -> int:
    if isinstance(value, list):
        value = value[0]
    return int(value)


class QuestionRepository:
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
                    WHERE qt_filter.question_id = q.question_id
                      AND qt_filter.tag_id = :tag_id
                )
                """
            )
            binds["tag_id"] = tag_id

        if status is not None:
            clauses.append("q.status = :status")
            binds["status"] = status

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

    def add_tags(
        self,
        connection: oracledb.Connection,
        question_id: int,
        tag_ids: list[int],
    ) -> None:
        if not tag_ids:
            return

        deduplicated_tag_ids = list(dict.fromkeys(tag_ids))
        rows = [{"question_id": question_id, "tag_id": tag_id} for tag_id in deduplicated_tag_ids]

        cursor = connection.cursor()
        cursor.executemany(
            """
            INSERT INTO question_tags (
                question_id,
                tag_id
            ) VALUES (
                :question_id,
                :tag_id
            )
            """,
            rows,
        )

    def get_question_detail(
        self,
        connection: oracledb.Connection,
        question_id: int,
    ) -> dict[str, Any] | None:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT q.question_id,
                   q.user_id,
                   q.category_id,
                   q.title,
                   q.content,
                   q.ask_time,
                   q.status,
                   q.view_count,
                   q.favorite_count,
                   q.answer_count,
                   u.username -- 🌟 1. SELECT 里加上 username
            FROM questions q
                     LEFT JOIN users u ON q.user_id = u.user_id -- 🌟 2. 加上连表查询
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
            "view_count": int(row[7]),
            "favorite_count": int(row[8]),
            "answer_count": int(row[9]),
            "username": row[10],  # 🌟 3. 新增这行：把查出的名字装进去
        }

        cursor.execute(
            """
            SELECT t.tag_id, t.tag_name
            FROM question_tags qt
            JOIN tags t
              ON t.tag_id = qt.tag_id
            WHERE qt.question_id = :question_id
            ORDER BY t.tag_name
            """,
            {"question_id": question_id},
        )
        question["tags"] = [
            {"tag_id": int(tag_row[0]), "tag_name": tag_row[1]}
            for tag_row in cursor.fetchall()
        ]

        return question

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
                u.username  -- 🌟 1. SELECT 里加上这行
            FROM questions q
            LEFT JOIN users u ON q.user_id = u.user_id  -- 🌟 2. FROM 后面加上连表查询
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
                "username": row[9],  # 🌟 3. 新增这行：把第10个字段（索引为9）装进 username
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

        return questions

    def get_question_list(self, connection) -> list[dict]:
        cursor = connection.cursor()
        # 用连表查询 (JOIN) 一次性把问题和发帖人的名字都查出来
        cursor.execute("""
                       SELECT q.question_id, q.title, q.content, q.ask_time, q.answer_count, u.username
                       FROM questions q
                                LEFT JOIN users u ON q.user_id = u.user_id
                       ORDER BY q.ask_time DESC
                       """)
        columns = [col[0].lower() for col in cursor.description]
        rows = cursor.fetchall()
        cursor.close()

        return [dict(zip(columns, row)) for row in rows]