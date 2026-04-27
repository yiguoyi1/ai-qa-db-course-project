from typing import Any

import oracledb


class UserCenterRepository:
    def user_exists(
        self,
        connection: oracledb.Connection,
        user_id: int,
    ) -> bool:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT 1
            FROM users
            WHERE user_id = :user_id
            """,
            {"user_id": user_id},
        )
        return cursor.fetchone() is not None

    @staticmethod
    def _attach_question_tags(
        connection: oracledb.Connection,
        items: list[dict[str, Any]],
        *,
        question_id_getter,
        tag_target_getter,
    ) -> None:
        if not items:
            return

        question_ids = list(dict.fromkeys(question_id_getter(item) for item in items))
        binds = {
            f"question_id_{index}": question_id
            for index, question_id in enumerate(question_ids)
        }
        placeholders = ", ".join(
            f":question_id_{index}" for index in range(len(question_ids))
        )

        cursor = connection.cursor()
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
            binds,
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
            tag_target_getter(item)["tags"] = tags_by_question_id.get(
                question_id_getter(item),
                [],
            )

    def get_user_profile(
        self,
        connection: oracledb.Connection,
        user_id: int,
    ) -> dict[str, Any] | None:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT
                u.user_id,
                u.username,
                u.nickname,
                u.email,
                u.phone,
                u.avatar_media_id,
                m.public_url,
                u.role,
                u.status,
                u.register_time,
                u.last_login_time,
                (SELECT COUNT(*)
                   FROM questions q
                  WHERE q.user_id = u.user_id) AS question_count,
                (SELECT COUNT(*)
                   FROM answers a
                  WHERE a.user_id = u.user_id) AS answer_count,
                (SELECT COUNT(*)
                   FROM favorites f
                  WHERE f.user_id = u.user_id) AS favorite_count,
                (SELECT COUNT(*)
                   FROM answers a
                   JOIN questions q
                     ON q.accepted_answer_id = a.answer_id
                  WHERE a.user_id = u.user_id) AS accepted_answer_count
            FROM users u
            LEFT JOIN media_assets m
              ON m.media_id = u.avatar_media_id
             AND m.status = 'ACTIVE'
            WHERE u.user_id = :user_id
            """,
            {"user_id": user_id},
        )
        row = cursor.fetchone()
        if row is None:
            return None

        return {
            "user_id": int(row[0]),
            "username": row[1],
            "nickname": row[2],
            "email": row[3],
            "phone": row[4],
            "avatar_media_id": int(row[5]) if row[5] is not None else None,
            "avatar_url": row[6],
            "role": row[7],
            "status": row[8],
            "register_time": row[9],
            "last_login_time": row[10],
            "question_count": int(row[11]),
            "answer_count": int(row[12]),
            "favorite_count": int(row[13]),
            "accepted_answer_count": int(row[14]),
        }

    def email_exists_for_other_user(
        self,
        connection: oracledb.Connection,
        *,
        email: str,
        user_id: int,
    ) -> bool:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT 1
            FROM users
            WHERE LOWER(email) = LOWER(:email)
              AND user_id <> :user_id
            FETCH FIRST 1 ROWS ONLY
            """,
            {
                "email": email,
                "user_id": user_id,
            },
        )
        return cursor.fetchone() is not None

    def phone_exists_for_other_user(
        self,
        connection: oracledb.Connection,
        *,
        phone: str,
        user_id: int,
    ) -> bool:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT 1
            FROM users
            WHERE phone = :phone
              AND user_id <> :user_id
            FETCH FIRST 1 ROWS ONLY
            """,
            {
                "phone": phone,
                "user_id": user_id,
            },
        )
        return cursor.fetchone() is not None

    def update_user_profile(
        self,
        connection: oracledb.Connection,
        *,
        user_id: int,
        nickname: str | None,
        email: str | None,
        phone: str | None,
    ) -> int:
        cursor = connection.cursor()
        cursor.execute(
            """
            UPDATE users
               SET nickname = :nickname,
                   email = :email,
                   phone = :phone
             WHERE user_id = :user_id
            """,
            {
                "nickname": nickname,
                "email": email,
                "phone": phone,
                "user_id": user_id,
            },
        )
        return int(cursor.rowcount or 0)

    def count_user_questions(
        self,
        connection: oracledb.Connection,
        *,
        user_id: int,
    ) -> int:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM questions
            WHERE user_id = :user_id
            """,
            {"user_id": user_id},
        )
        row = cursor.fetchone()
        return int(row[0]) if row is not None else 0

    def list_user_questions(
        self,
        connection: oracledb.Connection,
        *,
        user_id: int,
        page: int,
        page_size: int,
    ) -> list[dict[str, Any]]:
        cursor = connection.cursor()
        cursor.execute(
            """
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
              ON u.user_id = q.user_id
            LEFT JOIN media_assets m
              ON m.media_id = u.avatar_media_id
             AND m.status = 'ACTIVE'
            WHERE q.user_id = :user_id
            ORDER BY q.ask_time DESC, q.question_id DESC
            OFFSET :offset_rows ROWS FETCH NEXT :fetch_rows ROWS ONLY
            """,
            {
                "user_id": user_id,
                "offset_rows": (page - 1) * page_size,
                "fetch_rows": page_size,
            },
        )
        rows = cursor.fetchall()
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
                "username": row[9],
                "author_nickname": row[10],
                "author_avatar_url": row[11],
                "tags": [],
            }
            for row in rows
        ]
        self._attach_question_tags(
            connection,
            items,
            question_id_getter=lambda item: item["question_id"],
            tag_target_getter=lambda item: item,
        )
        return items

    def count_user_answers(
        self,
        connection: oracledb.Connection,
        *,
        user_id: int,
    ) -> int:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM answers
            WHERE user_id = :user_id
            """,
            {"user_id": user_id},
        )
        row = cursor.fetchone()
        return int(row[0]) if row is not None else 0

    def list_user_answers(
        self,
        connection: oracledb.Connection,
        *,
        user_id: int,
        page: int,
        page_size: int,
    ) -> list[dict[str, Any]]:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT
                a.answer_id,
                a.question_id,
                q.title,
                q.status,
                a.answer_type,
                a.provider_name,
                a.model_name,
                a.content,
                a.generate_time,
                a.confidence_score,
                a.like_count,
                a.dislike_count,
                a.avg_rating,
                CASE
                    WHEN q.accepted_answer_id = a.answer_id THEN 1
                    ELSE 0
                END AS is_accepted
            FROM answers a
            JOIN questions q
              ON q.question_id = a.question_id
            WHERE a.user_id = :user_id
            ORDER BY
                CASE
                    WHEN q.accepted_answer_id = a.answer_id THEN 0
                    ELSE 1
                END,
                a.generate_time DESC,
                a.answer_id DESC
            OFFSET :offset_rows ROWS FETCH NEXT :fetch_rows ROWS ONLY
            """,
            {
                "user_id": user_id,
                "offset_rows": (page - 1) * page_size,
                "fetch_rows": page_size,
            },
        )
        rows = cursor.fetchall()
        items = [
            {
                "answer_id": int(row[0]),
                "question": {
                    "question_id": int(row[1]),
                    "title": row[2],
                    "status": row[3],
                    "tags": [],
                },
                "answer_type": row[4],
                "provider_name": row[5],
                "model_name": row[6],
                "content": row[7].read() if hasattr(row[7], "read") else row[7],
                "generate_time": row[8],
                "confidence_score": float(row[9]) if row[9] is not None else None,
                "like_count": int(row[10]),
                "dislike_count": int(row[11]),
                "avg_rating": float(row[12]) if row[12] is not None else None,
                "is_accepted": bool(row[13]),
            }
            for row in rows
        ]
        self._attach_question_tags(
            connection,
            items,
            question_id_getter=lambda item: item["question"]["question_id"],
            tag_target_getter=lambda item: item["question"],
        )
        return items

    def count_user_favorites(
        self,
        connection: oracledb.Connection,
        *,
        user_id: int,
    ) -> int:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM favorites
            WHERE user_id = :user_id
            """,
            {"user_id": user_id},
        )
        row = cursor.fetchone()
        return int(row[0]) if row is not None else 0

    def list_user_favorites(
        self,
        connection: oracledb.Connection,
        *,
        user_id: int,
        page: int,
        page_size: int,
    ) -> list[dict[str, Any]]:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT
                f.favorite_id,
                f.favorite_time,
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
            FROM favorites f
            JOIN questions q
              ON q.question_id = f.question_id
            LEFT JOIN users u
              ON u.user_id = q.user_id
            LEFT JOIN media_assets m
              ON m.media_id = u.avatar_media_id
             AND m.status = 'ACTIVE'
            WHERE f.user_id = :user_id
            ORDER BY f.favorite_time DESC, f.favorite_id DESC
            OFFSET :offset_rows ROWS FETCH NEXT :fetch_rows ROWS ONLY
            """,
            {
                "user_id": user_id,
                "offset_rows": (page - 1) * page_size,
                "fetch_rows": page_size,
            },
        )
        rows = cursor.fetchall()
        items = [
            {
                "favorite_id": int(row[0]),
                "favorite_time": row[1],
                "question": {
                    "question_id": int(row[2]),
                    "user_id": int(row[3]),
                    "category_id": int(row[4]),
                    "title": row[5],
                    "ask_time": row[6],
                    "status": row[7],
                    "view_count": int(row[8]),
                    "favorite_count": int(row[9]),
                    "answer_count": int(row[10]),
                    "username": row[11],
                    "author_nickname": row[12],
                    "author_avatar_url": row[13],
                    "tags": [],
                },
            }
            for row in rows
        ]
        self._attach_question_tags(
            connection,
            items,
            question_id_getter=lambda item: item["question"]["question_id"],
            tag_target_getter=lambda item: item["question"],
        )
        return items

    def list_user_browse_history(
        self,
        connection: oracledb.Connection,
        *,
        user_id: int,
        limit: int,
    ) -> list[dict[str, Any]]:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT
                history_id,
                question_id,
                question_title,
                question_status,
                browse_time,
                duration,
                click_depth
            FROM (
                SELECT
                    bh.history_id,
                    q.question_id,
                    q.title AS question_title,
                    q.status AS question_status,
                    bh.browse_time,
                    bh.duration,
                    bh.click_depth,
                    ROW_NUMBER() OVER (
                        PARTITION BY q.question_id
                        ORDER BY bh.browse_time DESC, bh.history_id DESC
                    ) AS rn
                FROM browse_history bh
                JOIN questions q
                  ON q.question_id = bh.question_id
                WHERE bh.user_id = :user_id
            )
            WHERE rn = 1
            ORDER BY browse_time DESC, history_id DESC
            OFFSET 0 ROWS FETCH NEXT :limit ROWS ONLY
            """,
            {
                "user_id": user_id,
                "limit": limit,
            },
        )
        rows = cursor.fetchall()
        return [
            {
                "history_id": int(row[0]),
                "question_id": int(row[1]),
                "question_title": row[2],
                "question_status": row[3],
                "browse_time": row[4],
                "duration": int(row[5]),
                "click_depth": int(row[6]),
            }
            for row in rows
        ]

    def list_user_search_history(
        self,
        connection: oracledb.Connection,
        *,
        user_id: int,
        limit: int,
    ) -> list[dict[str, Any]]:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT
                keyword,
                MAX(search_time) AS last_search_time
            FROM search_history
            WHERE user_id = :user_id
            GROUP BY keyword
            ORDER BY last_search_time DESC, keyword
            OFFSET 0 ROWS FETCH NEXT :limit ROWS ONLY
            """,
            {
                "user_id": user_id,
                "limit": limit,
            },
        )
        rows = cursor.fetchall()
        return [
            {
                "keyword": row[0],
                "last_search_time": row[1],
            }
            for row in rows
        ]
