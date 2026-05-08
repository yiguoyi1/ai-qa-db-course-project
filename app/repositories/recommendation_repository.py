from typing import Any

import oracledb


class RecommendationRepository:
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

    def rebuild_user_tag_profile(
        self,
        connection: oracledb.Connection,
        user_id: int,
    ) -> None:
        cursor = connection.cursor()
        cursor.execute(
            """
            BEGIN
                qa_app_pkg.rebuild_user_tag_profile(:user_id);
            END;
            """,
            {"user_id": user_id},
        )

    def list_user_tag_profile(
        self,
        connection: oracledb.Connection,
        user_id: int,
    ) -> list[dict[str, Any]]:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT
                utp.tag_id,
                t.tag_name,
                utp.weight,
                utp.update_time
            FROM user_tag_profile utp
            JOIN tags t
              ON t.tag_id = utp.tag_id
             AND t.status = 'ACTIVE'
            WHERE utp.user_id = :user_id
            ORDER BY utp.weight DESC, t.tag_name
            """,
            {"user_id": user_id},
        )

        return [
            {
                "tag_id": int(row[0]),
                "tag_name": row[1],
                "weight": float(row[2]),
                "update_time": row[3],
            }
            for row in cursor.fetchall()
        ]

    def generate_recommendations(
        self,
        connection: oracledb.Connection,
        user_id: int,
        limit: int,
    ) -> None:
        cursor = connection.cursor()
        cursor.execute(
            """
            BEGIN
                qa_app_pkg.generate_recommendations(:user_id, :limit);
            END;
            """,
            {
                "user_id": user_id,
                "limit": limit,
            },
        )

    def count_recommendations(
        self,
        connection: oracledb.Connection,
        *,
        user_id: int,
        status: str,
    ) -> int:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM recommendations r
            JOIN questions q
              ON q.question_id = r.question_id
            JOIN categories c
              ON c.category_id = q.category_id
             AND c.status = 'ACTIVE'
            WHERE r.user_id = :user_id
              AND r.status = :status
              AND q.status <> 'DELETED'
            """,
            {
                "user_id": user_id,
                "status": status,
            },
        )
        row = cursor.fetchone()
        return int(row[0]) if row is not None else 0

    def list_recommendations(
        self,
        connection: oracledb.Connection,
        *,
        user_id: int,
        status: str,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        cursor = connection.cursor()
        limit_prefix = ""
        limit_suffix = ""
        binds: dict[str, Any] = {
            "user_id": user_id,
            "status": status,
        }
        if limit is not None:
            limit_prefix = "SELECT * FROM ("
            limit_suffix = ") WHERE ROWNUM <= :limit_rows"
            binds["limit_rows"] = limit

        cursor.execute(
            f"""
            {limit_prefix}
            SELECT
                r.rec_id,
                r.rec_type,
                r.rec_source,
                r.rec_reason,
                r.rec_score,
                r.rec_time,
                r.status AS rec_status,
                q.question_id,
                q.user_id,
                q.category_id,
                q.title,
                q.ask_time,
                q.status AS question_status,
                q.view_count,
                q.favorite_count,
                -- Derive visible answers at read time so soft-deleted rows do not
                -- leak through stale denormalized question counters.
                (
                    SELECT COUNT(*)
                    FROM answers a_count
                    WHERE a_count.question_id = q.question_id
                      AND a_count.status = 'ACTIVE'
                ) AS answer_count,
                u.username,
                u.nickname,
                m.public_url
            FROM recommendations r
            JOIN questions q
              ON q.question_id = r.question_id
            JOIN categories c
              ON c.category_id = q.category_id
             AND c.status = 'ACTIVE'
            LEFT JOIN users u
              ON u.user_id = q.user_id
            LEFT JOIN media_assets m
              ON m.media_id = u.avatar_media_id
             AND m.status = 'ACTIVE'
            WHERE r.user_id = :user_id
              AND r.status = :status
              AND q.status <> 'DELETED'
            ORDER BY r.rec_score DESC, r.rec_id DESC
            {limit_suffix}
            """,
            binds,
        )
        rows = cursor.fetchall()
        if not rows:
            return []

        question_ids = [int(row[7]) for row in rows]
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

        items: list[dict[str, Any]] = []
        for row in rows:
            question_id = int(row[7])
            items.append(
                {
                    "rec_id": int(row[0]),
                    "rec_type": row[1],
                    "rec_source": row[2],
                    "rec_reason": row[3],
                    "rec_score": float(row[4]),
                    "rec_time": row[5],
                    "status": row[6],
                    "question": {
                        "question_id": question_id,
                        "user_id": int(row[8]),
                        "category_id": int(row[9]),
                        "title": row[10],
                        "ask_time": row[11],
                        "status": row[12],
                        "view_count": int(row[13]),
                        "favorite_count": int(row[14]),
                        "answer_count": int(row[15]),
                        "username": row[16],
                        "author_nickname": row[17],
                        "author_avatar_url": row[18],
                        "tags": tags_by_question_id.get(question_id, []),
                    },
                }
            )

        return items
