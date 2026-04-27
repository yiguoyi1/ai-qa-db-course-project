from typing import Any

import oracledb


def _normalize_returning_value(value: Any) -> int:
    if isinstance(value, list):
        value = value[0]
    return int(value)


class TagRepository:
    def list_active_tags(
        self,
        connection: oracledb.Connection,
    ) -> list[dict[str, Any]]:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT tag_id, tag_name
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

    def get_tag_by_name(
        self,
        connection: oracledb.Connection,
        tag_name: str,
    ) -> dict[str, Any] | None:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT tag_id, tag_name, source, status
            FROM tags
            WHERE LOWER(tag_name) = LOWER(:tag_name)
            FETCH FIRST 1 ROWS ONLY
            """,
            {"tag_name": tag_name},
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return {
            "tag_id": int(row[0]),
            "tag_name": row[1],
            "source": row[2],
            "status": row[3],
        }

    def get_tags_by_ids(
        self,
        connection: oracledb.Connection,
        tag_ids: list[int],
    ) -> dict[int, dict[str, Any]]:
        if not tag_ids:
            return {}

        deduplicated_tag_ids = list(dict.fromkeys(tag_ids))
        binds = {
            f"tag_id_{index}": tag_id
            for index, tag_id in enumerate(deduplicated_tag_ids)
        }
        placeholders = ", ".join(f":tag_id_{index}" for index in range(len(deduplicated_tag_ids)))

        cursor = connection.cursor()
        cursor.execute(
            f"""
            SELECT tag_id, tag_name, source, status
            FROM tags
            WHERE tag_id IN ({placeholders})
            """,
            binds,
        )
        return {
            int(row[0]): {
                "tag_id": int(row[0]),
                "tag_name": row[1],
                "source": row[2],
                "status": row[3],
            }
            for row in cursor.fetchall()
        }

    def create_tag(
        self,
        connection: oracledb.Connection,
        *,
        tag_name: str,
        source: str,
        create_user_id: int | None = None,
        description: str | None = None,
        status: str = "ACTIVE",
    ) -> int:
        cursor = connection.cursor()
        tag_id_var = cursor.var(oracledb.NUMBER)
        cursor.execute(
            """
            INSERT INTO tags (
                tag_name,
                source,
                status,
                description,
                create_user_id
            ) VALUES (
                :tag_name,
                :source,
                :status,
                :description,
                :create_user_id
            )
            RETURNING tag_id INTO :tag_id
            """,
            {
                "tag_name": tag_name,
                "source": source,
                "status": status,
                "description": description,
                "create_user_id": create_user_id,
                "tag_id": tag_id_var,
            },
        )
        return _normalize_returning_value(tag_id_var.getvalue())

    def get_or_create_tag(
        self,
        connection: oracledb.Connection,
        *,
        tag_name: str,
        source: str,
        create_user_id: int | None = None,
        description: str | None = None,
    ) -> dict[str, Any]:
        existing = self.get_tag_by_name(connection, tag_name)
        if existing is not None:
            return existing

        tag_id = self.create_tag(
            connection,
            tag_name=tag_name,
            source=source,
            create_user_id=create_user_id,
            description=description,
        )
        return {
            "tag_id": tag_id,
            "tag_name": tag_name,
            "source": source,
            "status": "ACTIVE",
        }
