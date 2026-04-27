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
    ) -> list[dict[str, Any]]:
        cursor = connection.cursor()
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

        return [
            {
                "tag_id": int(row[0]),
                "tag_name": row[1],
            }
            for row in cursor.fetchall()
        ]
