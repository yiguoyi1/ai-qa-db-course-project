from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from app.services.auth_service import ALGORITHM, SECRET_KEY


_bearer_scheme = HTTPBearer(auto_error=False)


def _decode_current_user_id(
    credentials: HTTPAuthorizationCredentials | None,
    *,
    required: bool,
) -> int | None:
    if credentials is None:
        if required:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="请先登录后再执行该操作",
            )
        return None

    try:
        payload = jwt.decode(
            credentials.credentials,
            SECRET_KEY,
            algorithms=[ALGORITHM],
        )
        subject = payload.get("sub")
        if subject is None:
            raise ValueError("Missing sub claim.")
        return int(subject)
    except (JWTError, TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="房卡无效或已过期，请重新登录",
        ) from None


def get_current_user_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> int:
    user_id = _decode_current_user_id(credentials, required=True)
    assert user_id is not None
    return user_id


def get_optional_current_user_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> int | None:
    return _decode_current_user_id(credentials, required=False)


def resolve_authenticated_user_id(
    *,
    current_user_id: int,
    requested_user_id: int | None,
) -> int:
    if requested_user_id is not None and requested_user_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="user_id 与当前登录用户不一致",
        )
    return current_user_id


def resolve_tracking_user_id(
    *,
    current_user_id: int | None,
    requested_user_id: int | None,
) -> int | None:
    if current_user_id is None:
        if requested_user_id is not None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="记录搜索历史需要先登录",
            )
        return None

    if requested_user_id is not None and requested_user_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="user_id 与当前登录用户不一致",
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
            detail="只能访问当前登录用户自己的资源",
        )
    return current_user_id
