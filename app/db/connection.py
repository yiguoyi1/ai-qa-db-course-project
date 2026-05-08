from __future__ import annotations

from contextlib import contextmanager
from threading import Lock
from typing import Iterator

import oracledb

from app.core.errors import ConfigurationError
from app.core.settings import get_settings


_pool: oracledb.ConnectionPool | None = None
_pool_lock = Lock()


def _get_pool() -> oracledb.ConnectionPool:
    global _pool

    settings = get_settings()

    if not settings.app_user or not settings.app_user_password:
        raise ConfigurationError(
            "APP_USER and APP_USER_PASSWORD must be set before using the API."
        )
    if settings.oracle_pool_min <= 0:
        raise ConfigurationError("ORACLE_POOL_MIN must be greater than 0.")
    if settings.oracle_pool_max < settings.oracle_pool_min:
        raise ConfigurationError(
            "ORACLE_POOL_MAX must be greater than or equal to ORACLE_POOL_MIN."
        )
    if settings.oracle_pool_increment <= 0:
        raise ConfigurationError("ORACLE_POOL_INCREMENT must be greater than 0.")

    if _pool is None:
        with _pool_lock:
            if _pool is None:
                _pool = oracledb.create_pool(
                    user=settings.app_user,
                    password=settings.app_user_password,
                    dsn=settings.oracle_dsn,
                    min=settings.oracle_pool_min,
                    max=settings.oracle_pool_max,
                    increment=settings.oracle_pool_increment,
                )

    return _pool


@contextmanager
def get_connection() -> Iterator[oracledb.Connection]:
    connection = _get_pool().acquire()

    try:
        yield connection
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
