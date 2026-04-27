from typing import Any

import oracledb


class AdminRepository:
    @staticmethod
    def _build_user_filters(
        *,
        role: str | None,
        status: str | None,
    ) -> tuple[list[str], dict[str, Any]]:
        clauses = ["1 = 1"]
        binds: dict[str, Any] = {}

        if role is not None:
            clauses.append("role = :role")
            binds["role"] = role

        if status is not None:
            clauses.append("status = :status")
            binds["status"] = status

        return clauses, binds

    @staticmethod
    def _build_category_filters(
        *,
        status: str | None,
    ) -> tuple[list[str], dict[str, Any]]:
        clauses = ["1 = 1"]
        binds: dict[str, Any] = {}

        if status is not None:
            clauses.append("status = :status")
            binds["status"] = status

        return clauses, binds

    @staticmethod
    def _build_tag_filters(
        *,
        source: str | None,
        status: str | None,
        keyword: str | None,
    ) -> tuple[list[str], dict[str, Any]]:
        clauses = ["1 = 1"]
        binds: dict[str, Any] = {}

        if source is not None:
            clauses.append("t.source = :source")
            binds["source"] = source

        if status is not None:
            clauses.append("t.status = :status")
            binds["status"] = status

        if keyword is not None:
            clauses.append("LOWER(t.tag_name) LIKE :keyword")
            binds["keyword"] = f"%{keyword.lower()}%"

        return clauses, binds

    @staticmethod
    def _build_login_log_filters(
        *,
        user_id: int | None,
        result: str | None,
    ) -> tuple[list[str], dict[str, Any]]:
        clauses = ["1 = 1"]
        binds: dict[str, Any] = {}

        if user_id is not None:
            clauses.append("ll.user_id = :user_id")
            binds["user_id"] = user_id

        if result is not None:
            clauses.append("ll.result = :result")
            binds["result"] = result

        return clauses, binds

    @staticmethod
    def _build_operation_log_filters(
        *,
        user_id: int | None,
        op_type: str | None,
    ) -> tuple[list[str], dict[str, Any]]:
        clauses = ["1 = 1"]
        binds: dict[str, Any] = {}

        if user_id is not None:
            clauses.append("ol.user_id = :user_id")
            binds["user_id"] = user_id

        if op_type is not None:
            clauses.append("ol.op_type = :op_type")
            binds["op_type"] = op_type

        return clauses, binds

    def count_users(
        self,
        connection: oracledb.Connection,
        *,
        role: str | None = None,
        status: str | None = None,
    ) -> int:
        where_clauses, binds = self._build_user_filters(role=role, status=status)
        cursor = connection.cursor()
        cursor.execute(
            f"""
            SELECT COUNT(*)
            FROM users
            WHERE {' AND '.join(where_clauses)}
            """,
            binds,
        )
        row = cursor.fetchone()
        return int(row[0]) if row is not None else 0

    def list_users(
        self,
        connection: oracledb.Connection,
        *,
        page: int,
        page_size: int,
        role: str | None = None,
        status: str | None = None,
    ) -> list[dict[str, Any]]:
        where_clauses, binds = self._build_user_filters(role=role, status=status)
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
                user_id,
                username,
                nickname,
                email,
                phone,
                role,
                status,
                register_time,
                last_login_time
            FROM users
            WHERE {' AND '.join(where_clauses)}
            ORDER BY register_time DESC, user_id DESC
            OFFSET :offset_rows ROWS FETCH NEXT :fetch_rows ROWS ONLY
            """,
            binds,
        )

        rows = cursor.fetchall()
        return [
            {
                "user_id": int(row[0]),
                "username": row[1],
                "nickname": row[2],
                "email": row[3],
                "phone": row[4],
                "role": row[5],
                "status": row[6],
                "register_time": row[7],
                "last_login_time": row[8],
            }
            for row in rows
        ]

    def count_categories(
        self,
        connection: oracledb.Connection,
        *,
        status: str | None = None,
    ) -> int:
        where_clauses, binds = self._build_category_filters(status=status)
        cursor = connection.cursor()
        cursor.execute(
            f"""
            SELECT COUNT(*)
            FROM categories
            WHERE {' AND '.join(where_clauses)}
            """,
            binds,
        )
        row = cursor.fetchone()
        return int(row[0]) if row is not None else 0

    def list_categories(
        self,
        connection: oracledb.Connection,
        *,
        page: int,
        page_size: int,
        status: str | None = None,
    ) -> list[dict[str, Any]]:
        where_clauses, binds = self._build_category_filters(status=status)
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
                category_id,
                category_name,
                description,
                status
            FROM categories
            WHERE {' AND '.join(where_clauses)}
            ORDER BY category_name, category_id
            OFFSET :offset_rows ROWS FETCH NEXT :fetch_rows ROWS ONLY
            """,
            binds,
        )

        rows = cursor.fetchall()
        return [
            {
                "category_id": int(row[0]),
                "category_name": row[1],
                "description": row[2],
                "status": row[3],
            }
            for row in rows
        ]

    def get_category_context(
        self,
        connection: oracledb.Connection,
        category_id: int,
    ) -> dict[str, Any] | None:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT
                category_id,
                category_name,
                description,
                status
            FROM categories
            WHERE category_id = :category_id
            """,
            {"category_id": category_id},
        )
        row = cursor.fetchone()
        if row is None:
            return None

        return {
            "category_id": int(row[0]),
            "category_name": row[1],
            "description": row[2],
            "status": row[3],
        }

    def get_category_by_name(
        self,
        connection: oracledb.Connection,
        category_name: str,
    ) -> dict[str, Any] | None:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT
                category_id,
                category_name,
                description,
                status
            FROM categories
            WHERE category_name = :category_name
            """,
            {"category_name": category_name},
        )
        row = cursor.fetchone()
        if row is None:
            return None

        return {
            "category_id": int(row[0]),
            "category_name": row[1],
            "description": row[2],
            "status": row[3],
        }

    def create_category(
        self,
        connection: oracledb.Connection,
        *,
        category_name: str,
        description: str | None,
        status: str,
    ) -> int:
        cursor = connection.cursor()
        category_id_var = cursor.var(oracledb.NUMBER)
        cursor.execute(
            """
            INSERT INTO categories (
                category_name,
                description,
                status
            ) VALUES (
                :category_name,
                :description,
                :status
            )
            RETURNING category_id INTO :category_id
            """,
            {
                "category_name": category_name,
                "description": description,
                "status": status,
                "category_id": category_id_var,
            },
        )
        value = category_id_var.getvalue()
        return int(value[0] if isinstance(value, list) else value)

    def update_category(
        self,
        connection: oracledb.Connection,
        *,
        category_id: int,
        category_name: str,
        description: str | None,
        status: str,
    ) -> int:
        cursor = connection.cursor()
        cursor.execute(
            """
            UPDATE categories
            SET category_name = :category_name,
                description = :description,
                status = :status
            WHERE category_id = :category_id
            """,
            {
                "category_id": category_id,
                "category_name": category_name,
                "description": description,
                "status": status,
            },
        )
        return int(cursor.rowcount or 0)

    def count_tags(
        self,
        connection: oracledb.Connection,
        *,
        source: str | None = None,
        status: str | None = None,
        keyword: str | None = None,
    ) -> int:
        where_clauses, binds = self._build_tag_filters(
            source=source,
            status=status,
            keyword=keyword,
        )
        cursor = connection.cursor()
        cursor.execute(
            f"""
            SELECT COUNT(*)
            FROM tags t
            WHERE {' AND '.join(where_clauses)}
            """,
            binds,
        )
        row = cursor.fetchone()
        return int(row[0]) if row is not None else 0

    def list_tags(
        self,
        connection: oracledb.Connection,
        *,
        page: int,
        page_size: int,
        source: str | None = None,
        status: str | None = None,
        keyword: str | None = None,
    ) -> list[dict[str, Any]]:
        where_clauses, binds = self._build_tag_filters(
            source=source,
            status=status,
            keyword=keyword,
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
                t.tag_id,
                t.tag_name,
                t.source,
                t.status,
                t.description,
                t.create_user_id,
                u.username,
                t.create_time,
                COUNT(qt.qt_id) AS question_count
            FROM tags t
            LEFT JOIN users u
              ON u.user_id = t.create_user_id
            LEFT JOIN question_tags qt
              ON qt.tag_id = t.tag_id
            WHERE {' AND '.join(where_clauses)}
            GROUP BY
                t.tag_id,
                t.tag_name,
                t.source,
                t.status,
                t.description,
                t.create_user_id,
                u.username,
                t.create_time
            ORDER BY t.create_time DESC, t.tag_id DESC
            OFFSET :offset_rows ROWS FETCH NEXT :fetch_rows ROWS ONLY
            """,
            binds,
        )

        rows = cursor.fetchall()
        return [
            {
                "tag_id": int(row[0]),
                "tag_name": row[1],
                "source": row[2],
                "status": row[3],
                "description": row[4],
                "create_user_id": int(row[5]) if row[5] is not None else None,
                "create_username": row[6],
                "create_time": row[7],
                "question_count": int(row[8]),
            }
            for row in rows
        ]

    def get_tag_context(
        self,
        connection: oracledb.Connection,
        tag_id: int,
    ) -> dict[str, Any] | None:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT
                tag_id,
                tag_name,
                source,
                status,
                description
            FROM tags
            WHERE tag_id = :tag_id
            """,
            {"tag_id": tag_id},
        )
        row = cursor.fetchone()
        if row is None:
            return None

        return {
            "tag_id": int(row[0]),
            "tag_name": row[1],
            "source": row[2],
            "status": row[3],
            "description": row[4],
        }

    def get_tag_by_name(
        self,
        connection: oracledb.Connection,
        tag_name: str,
    ) -> dict[str, Any] | None:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT tag_id, tag_name, source, status, description
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
            "description": row[4],
        }

    def update_tag(
        self,
        connection: oracledb.Connection,
        *,
        tag_id: int,
        tag_name: str,
        description: str | None,
        status: str,
    ) -> int:
        cursor = connection.cursor()
        cursor.execute(
            """
            UPDATE tags
            SET tag_name = :tag_name,
                description = :description,
                status = :status
            WHERE tag_id = :tag_id
            """,
            {
                "tag_id": tag_id,
                "tag_name": tag_name,
                "description": description,
                "status": status,
            },
        )
        return int(cursor.rowcount or 0)

    def get_user_context(
        self,
        connection: oracledb.Connection,
        user_id: int,
    ) -> dict[str, Any] | None:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT
                user_id,
                username,
                role,
                status
            FROM users
            WHERE user_id = :user_id
            """,
            {"user_id": user_id},
        )
        row = cursor.fetchone()
        if row is None:
            return None

        return {
            "user_id": int(row[0]),
            "username": row[1],
            "role": row[2],
            "status": row[3],
        }

    def count_login_logs(
        self,
        connection: oracledb.Connection,
        *,
        user_id: int | None = None,
        result: str | None = None,
    ) -> int:
        where_clauses, binds = self._build_login_log_filters(
            user_id=user_id,
            result=result,
        )
        cursor = connection.cursor()
        cursor.execute(
            f"""
            SELECT COUNT(*)
            FROM login_log ll
            WHERE {' AND '.join(where_clauses)}
            """,
            binds,
        )
        row = cursor.fetchone()
        return int(row[0]) if row is not None else 0

    def list_login_logs(
        self,
        connection: oracledb.Connection,
        *,
        page: int,
        page_size: int,
        user_id: int | None = None,
        result: str | None = None,
    ) -> list[dict[str, Any]]:
        where_clauses, binds = self._build_login_log_filters(
            user_id=user_id,
            result=result,
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
                ll.log_id,
                ll.user_id,
                u.username,
                ll.login_time,
                ll.ip_address,
                ll.result
            FROM login_log ll
            LEFT JOIN users u
              ON u.user_id = ll.user_id
            WHERE {' AND '.join(where_clauses)}
            ORDER BY ll.login_time DESC, ll.log_id DESC
            OFFSET :offset_rows ROWS FETCH NEXT :fetch_rows ROWS ONLY
            """,
            binds,
        )
        rows = cursor.fetchall()
        return [
            {
                "log_id": int(row[0]),
                "user_id": int(row[1]),
                "username": row[2],
                "login_time": row[3],
                "ip_address": row[4],
                "result": row[5],
            }
            for row in rows
        ]

    def count_operation_logs(
        self,
        connection: oracledb.Connection,
        *,
        user_id: int | None = None,
        op_type: str | None = None,
    ) -> int:
        where_clauses, binds = self._build_operation_log_filters(
            user_id=user_id,
            op_type=op_type,
        )
        cursor = connection.cursor()
        cursor.execute(
            f"""
            SELECT COUNT(*)
            FROM operation_log ol
            WHERE {' AND '.join(where_clauses)}
            """,
            binds,
        )
        row = cursor.fetchone()
        return int(row[0]) if row is not None else 0

    def list_operation_logs(
        self,
        connection: oracledb.Connection,
        *,
        page: int,
        page_size: int,
        user_id: int | None = None,
        op_type: str | None = None,
    ) -> list[dict[str, Any]]:
        where_clauses, binds = self._build_operation_log_filters(
            user_id=user_id,
            op_type=op_type,
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
                ol.op_id,
                ol.user_id,
                u.username,
                ol.op_type,
                ol.op_content,
                ol.op_time
            FROM operation_log ol
            LEFT JOIN users u
              ON u.user_id = ol.user_id
            WHERE {' AND '.join(where_clauses)}
            ORDER BY ol.op_time DESC, ol.op_id DESC
            OFFSET :offset_rows ROWS FETCH NEXT :fetch_rows ROWS ONLY
            """,
            binds,
        )
        rows = cursor.fetchall()
        return [
            {
                "op_id": int(row[0]),
                "user_id": int(row[1]),
                "username": row[2],
                "op_type": row[3],
                "op_content": row[4],
                "op_time": row[5],
            }
            for row in rows
        ]

    def count_active_admin_users(
        self,
        connection: oracledb.Connection,
    ) -> int:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM users
            WHERE role = 'ADMIN'
              AND status = 'ACTIVE'
            """
        )
        row = cursor.fetchone()
        return int(row[0]) if row is not None else 0

    def update_user_status(
        self,
        connection: oracledb.Connection,
        *,
        user_id: int,
        status: str,
    ) -> int:
        cursor = connection.cursor()
        cursor.execute(
            """
            UPDATE users
            SET status = :status
            WHERE user_id = :user_id
            """,
            {"user_id": user_id, "status": status},
        )
        return int(cursor.rowcount or 0)

    def update_user_role(
        self,
        connection: oracledb.Connection,
        *,
        user_id: int,
        role: str,
    ) -> int:
        cursor = connection.cursor()
        cursor.execute(
            """
            UPDATE users
            SET role = :role
            WHERE user_id = :user_id
            """,
            {"user_id": user_id, "role": role},
        )
        return int(cursor.rowcount or 0)

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

    def get_comment_context(
        self,
        connection: oracledb.Connection,
        comment_id: int,
    ) -> dict[str, Any] | None:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT
                comment_id,
                answer_id,
                user_id,
                status
            FROM answer_comments
            WHERE comment_id = :comment_id
            """,
            {"comment_id": comment_id},
        )
        row = cursor.fetchone()
        if row is None:
            return None

        return {
            "comment_id": int(row[0]),
            "answer_id": int(row[1]),
            "user_id": int(row[2]),
            "status": row[3],
        }

    def update_comment_status(
        self,
        connection: oracledb.Connection,
        *,
        comment_id: int,
        status: str,
    ) -> int:
        cursor = connection.cursor()
        if status == "DELETED":
            cursor.execute(
                """
                UPDATE answer_comments
                SET status = 'DELETED',
                    update_time = SYSDATE,
                    delete_time = SYSDATE
                WHERE comment_id = :comment_id
                """,
                {"comment_id": comment_id},
            )
        else:
            cursor.execute(
                """
                UPDATE answer_comments
                SET status = :status,
                    update_time = SYSDATE,
                    delete_time = NULL
                WHERE comment_id = :comment_id
                """,
                {"comment_id": comment_id, "status": status},
            )
        return int(cursor.rowcount or 0)
