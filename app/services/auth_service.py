from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import jwt

from app.core.errors import AppError, ValidationError, NotFoundError
from app.db.connection import get_connection
from app.repositories.user_repository import UserRepository
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse

# 密码加密器：使用 bcrypt 算法
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT 印钞机配置（在企业里这些要写进 .env 里，现在为了测试先写死）
SECRET_KEY = "super-secret-ai-qa-key-do-not-leak"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 房卡有效期：7天

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
        with get_connection() as connection:
            # 1. 去数据库里找这个人
            user = self._user_repository.get_user_by_username(connection, payload.username)
            if not user:
                raise NotFoundError("用户名或密码错误") # 故意不告诉黑客是用户名错还是密码错

            # 2. 核心操作：验证密码。用加密器核对明文和数据库里的乱码是否匹配
            if not pwd_context.verify(payload.password, user["password_hash"]):
                raise ValidationError("用户名或密码错误")

            # 3. 登录成功！开始印制 JWT 房卡 (Token)
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            # 房卡里藏着用户信息和过期时间
            to_encode = {"sub": str(user["user_id"]), "exp": expire}
            encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

            # 4. 把发好的房卡端给服务员
            return TokenResponse(
                access_token=encoded_jwt,
                user_id=user["user_id"]
            )