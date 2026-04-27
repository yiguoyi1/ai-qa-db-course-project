from typing import Any

import oracledb


class SearchRepository:
    @staticmethod
    def _attach_favorite_state(
        connection: oracledb.Connection,
        items: list[dict[str, Any]],
        *,
        current_user_id: int | None,
    ) -> None:
        if not items:
            return

        if current_user_id is None:
            for item in items:
                item["is_favorited"] = False
            return

        question_ids = [item["question_id"] for item in items]
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
            item["is_favorited"] = item["question_id"] in favorited_question_ids

    @staticmethod
    def _build_search_filters(
        *,
        keyword: str,
        category_id: int | None,
        tag_id: int | None,
        status: str | None,
    ) -> tuple[list[str], dict[str, Any]]:
        clauses = [
            """
            (
                LOWER(q.title) LIKE :keyword_like
                OR DBMS_LOB.INSTR(LOWER(q.content), LOWER(:keyword)) > 0
            )
            """
        ]
        binds: dict[str, Any] = {
            "keyword": keyword,
            "keyword_like": f"%{keyword.lower()}%",
        }

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

    def create_search_history(
        self,
        connection: oracledb.Connection,
        *,
        user_id: int,
        keyword: str,
    ) -> None:
        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT INTO search_history (
                user_id,
                keyword
            ) VALUES (
                :user_id,
                :keyword
            )
            """,
            {
                "user_id": user_id,
                "keyword": keyword,
            },
        )

    def count_search_results(
        self,
        connection: oracledb.Connection,
        *,
        keyword: str,
        category_id: int | None = None,
        tag_id: int | None = None,
        status: str | None = None,
    ) -> int:
        where_clauses, binds = self._build_search_filters(
            keyword=keyword,
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

    def search_questions(
        self,
        connection: oracledb.Connection,
        *,
        keyword: str,
        page: int,
        page_size: int,
        current_user_id: int | None = None,
        category_id: int | None = None,
        tag_id: int | None = None,
        status: str | None = None,
    ) -> list[dict[str, Any]]:
        where_clauses, binds = self._build_search_filters(
            keyword=keyword,
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
                u.username,  -- 🌟 1. SELECT 里多查一列：用户表里的名字
                u.nickname,
                m.public_url
            FROM questions q
            LEFT JOIN users u ON q.user_id = u.user_id -- 🌟 2. 关键：把用户表连进来！
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

        items = [
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
                "username": row[9],  # 🌟 3. 别忘了把第 10 列（索引是9）的名字装进字典里发给前端！
                "author_nickname": row[10],
                "author_avatar_url": row[11],
                "is_favorited": False,
                "tags": [],
            }
            for row in rows
        ]

        question_ids = [item["question_id"] for item in items]
        tag_binds = {
            f"question_id_{index}": question_id
            for index, question_id in enumerate(question_ids)
        }
        placeholders = ", ".join(
            f":question_id_{index}" for index in range(len(question_ids))
        )

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

        for item in items:
            item["tags"] = tags_by_question_id.get(item["question_id"], [])

        self._attach_favorite_state(
            connection,
            items,
            current_user_id=current_user_id,
        )

        return items

    # 🌟 新增：获取用户最近的 5 条不重复搜索历史
    def get_search_history(self, connection: oracledb.Connection, user_id: int, limit: int = 5) -> list[str]:
        cursor = connection.cursor()
        # 利用 MAX(rowid) 巧妙获取最新插入的记录，并去重
        cursor.execute(
            """
            SELECT keyword
            FROM search_history
            WHERE user_id = :user_id
            GROUP BY keyword
            ORDER BY MAX(rowid) DESC
            OFFSET 0 ROWS FETCH NEXT :limit ROWS ONLY
            """,
            {"user_id": user_id, "limit": limit}
        )
        # 把结果拼成一个单纯的字符串列表返回给前端，比如：["考研", "Python", "FastAPI"]
        return [row[0] for row in cursor.fetchall()]
