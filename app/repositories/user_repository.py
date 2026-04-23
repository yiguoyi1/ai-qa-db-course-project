import oracledb


class UserRepository:
    @staticmethod
    def _build_user_record(row: tuple) -> dict:
        return {
            "user_id": int(row[0]),
            "username": row[1],
            "password_hash": row[2],
            "status": row[3],
            "role": row[4],
            "nickname": row[5],
        }

    def get_user_by_username(self, connection, username: str) -> dict | None:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT user_id, username, password_hash, status, role, nickname
            FROM users
            WHERE username = :1
            """,
            [username],
        )
        row = cursor.fetchone()
        cursor.close()

        return self._build_user_record(row) if row else None

    def get_user_by_id(self, connection, user_id: int) -> dict | None:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT user_id, username, password_hash, status, role, nickname
            FROM users
            WHERE user_id = :1
            """,
            [user_id],
        )
        row = cursor.fetchone()
        cursor.close()

        return self._build_user_record(row) if row else None

    def create_user(self, connection, username: str, password_hash: str, nickname: str | None) -> int:
        cursor = connection.cursor()
        user_id_var = cursor.var(int)

        cursor.execute(
            """
            INSERT INTO users (username, password_hash, nickname)
            VALUES (:1, :2, :3) RETURNING user_id
            INTO :4
            """,
            [username, password_hash, nickname, user_id_var],
        )
        user_id = user_id_var.getvalue()[0]
        cursor.close()
        return int(user_id)
