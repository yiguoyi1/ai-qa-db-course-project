from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import jwt

from app.core.settings import JWT_SECRET_PLACEHOLDER, get_settings
from app.core.errors import AppError, ValidationError
from app.db.connection import get_connection
from app.repositories.log_repository import LogRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse

# 密码加密器：使用 bcrypt 算法
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _get_jwt_config() -> tuple[str, str, int]:
    settings = get_settings()

    if not settings.jwt_secret_key:
        raise AppError("JWT_SECRET_KEY 未配置，请先在 .env 中设置该项。", status_code=500)
    if settings.jwt_secret_key == JWT_SECRET_PLACEHOLDER or len(settings.jwt_secret_key) < 32:
        raise AppError(
            "JWT_SECRET_KEY 必须是当前环境专用的强随机密钥，且长度至少为 32 个字符。",
            status_code=500,
        )
    if not settings.jwt_algorithm:
        raise AppError("JWT_ALGORITHM 未配置，请先在 .env 中设置该项。", status_code=500)
    if settings.jwt_access_token_expire_minutes <= 0:
        raise AppError(
            "JWT_ACCESS_TOKEN_EXPIRE_MINUTES 必须大于 0。",
            status_code=500,
        )

    return (
        settings.jwt_secret_key,
        settings.jwt_algorithm,
        settings.jwt_access_token_expire_minutes,
    )

class AuthService:
    def __init__(
        self,
        user_repository: UserRepository | None = None,
        log_repository: LogRepository | None = None,
    ):
        self._user_repository = user_repository or UserRepository()
        self._log_repository = log_repository or LogRepository()

    def register(self, payload: RegisterRequest) -> dict:
        with get_connection() as connection:
            # 1. 检查用户名是否被占用了
            existing_user = self._user_repository.get_user_by_username(connection, payload.username)
            if existing_user:
                raise ValidationError("该用户名已被注册，请换一个试试！")

            # 2. 核心操作：把密码变成乱码（哈希加密）
            hashed_password = pwd_context.hash(payload.password)

            # 3. 存入数据库
            user_id = self._user_repository.create_user(
                connection=connection,
                username=payload.username,
                password_hash=hashed_password,
                nickname=payload.nickname
            )
            connection.commit()
            return {"user_id": user_id, "message": "注册成功"}

    def login(self, payload: LoginRequest, *, ip_address: str | None = None) -> TokenResponse:
        secret_key, algorithm, access_token_expire_minutes = _get_jwt_config()

        with get_connection() as connection:
            # 1. 去数据库里找这个人
            user = self._user_repository.get_user_by_username(connection, payload.username)
            if not user:
                raise ValidationError("用户名或密码错误") # 故意不告诉黑客是用户名错还是密码错

            status_error = self._get_login_status_error(user["status"])
            if status_error is not None:
                self._log_login_attempt(
                    connection=connection,
                    user_id=user["user_id"],
                    ip_address=ip_address,
                    result="LOCKED" if user["status"] == "LOCKED" else "FAILURE",
                )
                connection.commit()
                raise status_error

            # 2. 核心操作：验证密码。用加密器核对明文和数据库里的乱码是否匹配
            if not pwd_context.verify(payload.password, user["password_hash"]):
                self._log_login_attempt(
                    connection=connection,
                    user_id=user["user_id"],
                    ip_address=ip_address,
                    result="FAILURE",
                )
                connection.commit()
                raise ValidationError("用户名或密码错误")

            # 3. 登录成功！开始印制 JWT 房卡 (Token)
            expire = datetime.utcnow() + timedelta(minutes=access_token_expire_minutes)
            # 房卡里藏着用户信息和过期时间
            to_encode = {"sub": str(user["user_id"]), "exp": expire}
            encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=algorithm)
            self._log_login_attempt(
                connection=connection,
                user_id=user["user_id"],
                ip_address=ip_address,
                result="SUCCESS",
            )
            connection.commit()

            # 4. 把发好的房卡端给服务员
            return TokenResponse(
                access_token=encoded_jwt,
                user_id=user["user_id"],
                username=user["username"],
                role=user["role"],
            )

    def _log_login_attempt(
        self,
        *,
        connection,
        user_id: int,
        ip_address: str | None,
        result: str,
    ) -> None:
        self._log_repository.create_login_log(
            connection=connection,
            user_id=user_id,
            ip_address=ip_address,
            result=result,
        )

    @staticmethod
    def _get_login_status_error(user_status: str) -> AppError | None:
        if user_status == "ACTIVE":
            return None
        if user_status == "LOCKED":
            return AppError("账号已锁定，请联系管理员处理。", status_code=423)
        if user_status == "DISABLED":
            return AppError("账号已停用，无法登录。", status_code=403)
        if user_status == "INACTIVE":
            return AppError("账号未激活或暂不可用，请联系管理员。", status_code=403)

        return AppError(f"账号状态异常：{user_status}", status_code=403)
