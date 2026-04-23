from typing import Any

import oracledb


def _normalize_returning_value(value: Any) -> int:
    if isinstance(value, list):
        value = value[0]
    return int(value)


class MediaRepository:
    def create_media_asset(
        self,
        connection: oracledb.Connection,
        *,
        uploader_user_id: int,
        owner_type: str,
        owner_id: int,
        file_name: str,
        original_file_name: str | None,
        mime_type: str,
        file_ext: str | None,
        file_size: int,
        storage_path: str,
        public_url: str,
        sort_order: int = 1,
        status: str = "ACTIVE",
    ) -> int:
        cursor = connection.cursor()
        media_id_var = cursor.var(oracledb.NUMBER)
        cursor.execute(
            """
            INSERT INTO media_assets (
                uploader_user_id,
                owner_type,
                owner_id,
                file_name,
                original_file_name,
                mime_type,
                file_ext,
                file_size,
                storage_path,
                public_url,
                sort_order,
                status
            ) VALUES (
                :uploader_user_id,
                :owner_type,
                :owner_id,
                :file_name,
                :original_file_name,
                :mime_type,
                :file_ext,
                :file_size,
                :storage_path,
                :public_url,
                :sort_order,
                :status
            )
            RETURNING media_id INTO :media_id
            """,
            {
                "uploader_user_id": uploader_user_id,
                "owner_type": owner_type,
                "owner_id": owner_id,
                "file_name": file_name,
                "original_file_name": original_file_name,
                "mime_type": mime_type,
                "file_ext": file_ext,
                "file_size": file_size,
                "storage_path": storage_path,
                "public_url": public_url,
                "sort_order": sort_order,
                "status": status,
                "media_id": media_id_var,
            },
        )
        return _normalize_returning_value(media_id_var.getvalue())

    def get_active_avatar_by_user_id(
        self,
        connection: oracledb.Connection,
        user_id: int,
    ) -> dict[str, Any] | None:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT
                m.media_id,
                m.uploader_user_id,
                m.owner_type,
                m.owner_id,
                m.file_name,
                m.original_file_name,
                m.mime_type,
                m.file_ext,
                m.file_size,
                m.storage_path,
                m.public_url,
                m.sort_order,
                m.status,
                m.create_time,
                m.update_time,
                m.delete_time
            FROM users u
            JOIN media_assets m
              ON m.media_id = u.avatar_media_id
            WHERE u.user_id = :user_id
              AND m.status = 'ACTIVE'
            """,
            {"user_id": user_id},
        )
        row = cursor.fetchone()
        if row is None:
            return None

        return {
            "media_id": int(row[0]),
            "uploader_user_id": int(row[1]),
            "owner_type": row[2],
            "owner_id": int(row[3]),
            "file_name": row[4],
            "original_file_name": row[5],
            "mime_type": row[6],
            "file_ext": row[7],
            "file_size": int(row[8]),
            "storage_path": row[9],
            "public_url": row[10],
            "sort_order": int(row[11]),
            "status": row[12],
            "create_time": row[13],
            "update_time": row[14],
            "delete_time": row[15],
        }

    def count_active_media_by_owner(
        self,
        connection: oracledb.Connection,
        *,
        owner_type: str,
        owner_id: int,
    ) -> int:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM media_assets
            WHERE owner_type = :owner_type
              AND owner_id = :owner_id
              AND status = 'ACTIVE'
            """,
            {
                "owner_type": owner_type,
                "owner_id": owner_id,
            },
        )
        row = cursor.fetchone()
        return int(row[0]) if row is not None else 0

    def get_next_sort_order_for_owner(
        self,
        connection: oracledb.Connection,
        *,
        owner_type: str,
        owner_id: int,
    ) -> int:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT NVL(MAX(sort_order), 0) + 1
            FROM media_assets
            WHERE owner_type = :owner_type
              AND owner_id = :owner_id
            """,
            {
                "owner_type": owner_type,
                "owner_id": owner_id,
            },
        )
        row = cursor.fetchone()
        return int(row[0]) if row is not None else 1

    def list_active_media_by_owner(
        self,
        connection: oracledb.Connection,
        *,
        owner_type: str,
        owner_id: int,
    ) -> list[dict[str, Any]]:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT
                media_id,
                uploader_user_id,
                owner_type,
                owner_id,
                file_name,
                original_file_name,
                mime_type,
                file_ext,
                file_size,
                storage_path,
                public_url,
                sort_order,
                status,
                create_time,
                update_time,
                delete_time
            FROM media_assets
            WHERE owner_type = :owner_type
              AND owner_id = :owner_id
              AND status = 'ACTIVE'
            ORDER BY sort_order, media_id
            """,
            {
                "owner_type": owner_type,
                "owner_id": owner_id,
            },
        )
        return [self._build_media_record(row) for row in cursor.fetchall()]

    def get_active_media_by_id(
        self,
        connection: oracledb.Connection,
        *,
        media_id: int,
        owner_type: str | None = None,
        owner_id: int | None = None,
    ) -> dict[str, Any] | None:
        clauses = ["media_id = :media_id", "status = 'ACTIVE'"]
        binds: dict[str, Any] = {"media_id": media_id}

        if owner_type is not None:
            clauses.append("owner_type = :owner_type")
            binds["owner_type"] = owner_type
        if owner_id is not None:
            clauses.append("owner_id = :owner_id")
            binds["owner_id"] = owner_id

        cursor = connection.cursor()
        cursor.execute(
            f"""
            SELECT
                media_id,
                uploader_user_id,
                owner_type,
                owner_id,
                file_name,
                original_file_name,
                mime_type,
                file_ext,
                file_size,
                storage_path,
                public_url,
                sort_order,
                status,
                create_time,
                update_time,
                delete_time
            FROM media_assets
            WHERE {' AND '.join(clauses)}
            """,
            binds,
        )
        row = cursor.fetchone()
        return self._build_media_record(row) if row is not None else None

    def update_user_avatar_media(
        self,
        connection: oracledb.Connection,
        *,
        user_id: int,
        media_id: int | None,
    ) -> int:
        cursor = connection.cursor()
        cursor.execute(
            """
            UPDATE users
            SET avatar_media_id = :media_id
            WHERE user_id = :user_id
            """,
            {
                "user_id": user_id,
                "media_id": media_id,
            },
        )
        return int(cursor.rowcount or 0)

    def mark_media_deleted(
        self,
        connection: oracledb.Connection,
        *,
        media_id: int,
    ) -> int:
        cursor = connection.cursor()
        cursor.execute(
            """
            UPDATE media_assets
            SET status = 'DELETED',
                update_time = SYSDATE,
                delete_time = SYSDATE
            WHERE media_id = :media_id
              AND status <> 'DELETED'
            """,
            {"media_id": media_id},
        )
        return int(cursor.rowcount or 0)

    @staticmethod
    def _build_media_record(row: tuple[Any, ...]) -> dict[str, Any]:
        return {
            "media_id": int(row[0]),
            "uploader_user_id": int(row[1]),
            "owner_type": row[2],
            "owner_id": int(row[3]),
            "file_name": row[4],
            "original_file_name": row[5],
            "mime_type": row[6],
            "file_ext": row[7],
            "file_size": int(row[8]),
            "storage_path": row[9],
            "public_url": row[10],
            "sort_order": int(row[11]),
            "status": row[12],
            "create_time": row[13],
            "update_time": row[14],
            "delete_time": row[15],
        }
