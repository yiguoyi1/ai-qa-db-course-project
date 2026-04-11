import oracledb


class UserRepository:
    # 动作 1：根据用户名找人（用于登录和防重复注册）
    def get_user_by_username(self, connection, username: str) -> dict | None:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT user_id, username, password_hash, status
            FROM users
            WHERE username = :1
            """,
            [username]
        )
        row = cursor.fetchone()
        cursor.close()

        if row:
            return {
                "user_id": row[0],
                "username": row[1],
                "password_hash": row[2],
                "status": row[3]
            }
        return None

    # 动作 2：创建新用户（用于注册）
    def create_user(self, connection, username: str, password_hash: str, nickname: str | None) -> int:
        cursor = connection.cursor()
        # Oracle 特有的返回新插入 ID 的写法 (RETURNING ... INTO ...)
        user_id_var = cursor.var(int)

        cursor.execute(
            """
            INSERT INTO users (username, password_hash, nickname)
            VALUES (:1, :2, :3) RETURNING user_id
            INTO :4
            """,
            [username, password_hash, nickname, user_id_var]
        )
        user_id = user_id_var.getvalue()[0]
        cursor.close()
        return int(user_id)