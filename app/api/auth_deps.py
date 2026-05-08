from dataclasses import dataclass

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from app.core.settings import JWT_SECRET_PLACEHOLDER, get_settings
from app.db.connection import get_connection
from app.repositories.user_repository import UserRepository


_bearer_scheme = HTTPBearer(auto_error=False)
_user_repository = UserRepository()


@dataclass(frozen=True)
class AuthenticatedUser:
    user_id: int
    username: str
    role: str
    status: str
    nickname: str | None = None


def _get_decode_config() -> tuple[str, str]:
    settings = get_settings()

    if not settings.jwt_secret_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="JWT_SECRET_KEY 未配置，请联系管理员检查服务配置。",
        )
    if settings.jwt_secret_key == JWT_SECRET_PLACEHOLDER or len(settings.jwt_secret_key) < 32:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="JWT_SECRET_KEY 必须为当前环境单独配置，且长度至少为 32 个字符。",
        )
    if not settings.jwt_algorithm:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="JWT_ALGORITHM 未配置，请联系管理员检查服务配置。",
        )

    return settings.jwt_secret_key, settings.jwt_algorithm


def _decode_current_user_id(
    credentials: HTTPAuthorizationCredentials | None,
    *,
    required: bool,
) -> int | None:
    if credentials is None:
        if required:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="请先登录后再执行该操作。",
            )
        return None

    try:
        secret_key, algorithm = _get_decode_config()
        payload = jwt.decode(
            credentials.credentials,
            secret_key,
            algorithms=[algorithm],
        )
        subject = payload.get("sub")
        if subject is None:
            raise ValueError("Missing sub claim.")
        return int(subject)
    except (JWTError, TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="登录令牌无效或已过期，请重新登录。",
        ) from None


def _load_current_user(user_id: int) -> AuthenticatedUser:
    with get_connection() as connection:
        user = _user_repository.get_user_by_id(connection, user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="当前登录用户不存在，请重新登录。",
        )

    return AuthenticatedUser(
        user_id=user["user_id"],
        username=user["username"],
        role=user["role"],
        status=user["status"],
        nickname=user.get("nickname"),
    )


def _ensure_current_user_is_active(user: AuthenticatedUser) -> AuthenticatedUser:
    if user.status == "ACTIVE":
        return user
    if user.status == "LOCKED":
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail="账号已锁定，暂时无法继续操作。",
        )
    if user.status == "DISABLED":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账号已停用，无法继续操作。",
        )
    if user.status == "INACTIVE":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账号未激活或暂不可用。",
        )

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=f"账号状态异常：{user.status}",
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> AuthenticatedUser:
    user_id = _decode_current_user_id(credentials, required=True)
    assert user_id is not None
    return _ensure_current_user_is_active(_load_current_user(user_id))


def get_current_user_id(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> int:
    return current_user.user_id


def get_admin_user(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> AuthenticatedUser:
    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以访问该资源。",
        )
    return current_user


def get_admin_user_id(
    admin_user: AuthenticatedUser = Depends(get_admin_user),
) -> int:
    return admin_user.user_id


def get_optional_current_user_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> int | None:
    try:
        user_id = _decode_current_user_id(credentials, required=False)
    except HTTPException as exc:
        if exc.status_code == status.HTTP_401_UNAUTHORIZED:
            return None
        raise
    if user_id is None:
        return None
    try:
        return _ensure_current_user_is_active(_load_current_user(user_id)).user_id
    except HTTPException as exc:
        if exc.status_code in {
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
            status.HTTP_423_LOCKED,
        }:
            return None
        raise


def resolve_authenticated_user_id(
    *,
    current_user_id: int,
    requested_user_id: int | None,
) -> int:
    if requested_user_id is not None and requested_user_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="user_id 与当前登录用户不一致。",
        )
    return current_user_id


def ensure_path_user_access(
    *,
    path_user_id: int,
    current_user_id: int,
) -> int:
    if path_user_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只能访问当前登录用户自己的资源。",
        )
    return current_user_id
