from typing import Any

import oracledb


class MetaRepository:
    def list_categories(
        self,
        connection: oracledb.Connection,
    ) -> list[dict[str, Any]]:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT
                category_id,
                category_name,
                description,
                status
            FROM categories
            WHERE status = 'ACTIVE'
            ORDER BY category_name
            """
        )

        return [
            {
                "category_id": int(row[0]),
                "category_name": row[1],
                "description": row[2],
                "status": row[3],
            }
            for row in cursor.fetchall()
        ]

    def list_tags(
        self,
        connection: oracledb.Connection,
        *,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        cursor = connection.cursor()
        if limit is None:
            cursor.execute(
                """
                SELECT
                    tag_id,
                    tag_name
                FROM tags
                WHERE status = 'ACTIVE'
                ORDER BY tag_name
                """
            )
        else:
            cursor.execute(
                """
                SELECT
                    tag_id,
                    tag_name
                FROM (
                    SELECT
                        tag_id,
                        tag_name
                    FROM tags
                    WHERE status = 'ACTIVE'
                    ORDER BY tag_name
                )
                WHERE ROWNUM <= :limit_rows
                """,
                {"limit_rows": limit},
            )

        return [
            {
                "tag_id": int(row[0]),
                "tag_name": row[1],
            }
            for row in cursor.fetchall()
        ]

    def suggest_tags(
        self,
        connection: oracledb.Connection,
        *,
        keyword: str | None,
        limit: int,
    ) -> list[dict[str, Any]]:
        cursor = connection.cursor()
        keyword_like = f"%{keyword}%" if keyword is not None else None
        keyword_prefix = f"{keyword}%" if keyword is not None else None
        cursor.execute(
            """
            SELECT
                t.tag_id,
                t.tag_name,
                COUNT(qt.qt_id) AS question_count
            FROM tags t
            LEFT JOIN question_tags qt
              ON qt.tag_id = t.tag_id
            WHERE t.status = 'ACTIVE'
              AND (:keyword_like IS NULL OR LOWER(t.tag_name) LIKE :keyword_like)
            GROUP BY
                t.tag_id,
                t.tag_name
            ORDER BY
                CASE
                    WHEN :keyword IS NOT NULL AND LOWER(t.tag_name) = :keyword THEN 0
                    WHEN :keyword_prefix IS NOT NULL AND LOWER(t.tag_name) LIKE :keyword_prefix THEN 1
                    ELSE 2
                END,
                COUNT(qt.qt_id) DESC,
                t.tag_name
            FETCH FIRST :limit_rows ROWS ONLY
            """,
            {
                "keyword": keyword,
                "keyword_like": keyword_like,
                "keyword_prefix": keyword_prefix,
                "limit_rows": limit,
            },
        )

        return [
            {
                "tag_id": int(row[0]),
                "tag_name": row[1],
                "question_count": int(row[2]),
            }
            for row in cursor.fetchall()
        ]
