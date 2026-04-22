from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import jwt

from app.core.settings import get_settings
from app.core.errors import AppError, ValidationError, NotFoundError
from app.db.connection import get_connection
from app.repositories.user_repository import UserRepository
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse

# 密码加密器：使用 bcrypt 算法
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _get_jwt_config() -> tuple[str, str, int]:
    settings = get_settings()

    if not settings.jwt_secret_key:
        raise AppError("JWT_SECRET_KEY 未配置，请先在 .env 中设置该项。", status_code=500)
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
    def __init__(self, user_repository: UserRepository | None = None):
        self._user_repository = user_repository or UserRepository()

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

    def login(self, payload: LoginRequest) -> TokenResponse:
        secret_key, algorithm, access_token_expire_minutes = _get_jwt_config()

        with get_connection() as connection:
            # 1. 去数据库里找这个人
            user = self._user_repository.get_user_by_username(connection, payload.username)
            if not user:
                raise NotFoundError("用户名或密码错误") # 故意不告诉黑客是用户名错还是密码错

            # 2. 核心操作：验证密码。用加密器核对明文和数据库里的乱码是否匹配
            if not pwd_context.verify(payload.password, user["password_hash"]):
                raise ValidationError("用户名或密码错误")

            # 3. 登录成功！开始印制 JWT 房卡 (Token)
            expire = datetime.utcnow() + timedelta(minutes=access_token_expire_minutes)
            # 房卡里藏着用户信息和过期时间
            to_encode = {"sub": str(user["user_id"]), "exp": expire}
            encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=algorithm)

            # 4. 把发好的房卡端给服务员
            return TokenResponse(
                access_token=encoded_jwt,
                user_id=user["user_id"],
                username=user["username"]
            )
