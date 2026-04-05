from contextlib import contextmanager
from typing import Iterator

import oracledb

from app.core.errors import ConfigurationError
from app.core.settings import get_settings


@contextmanager
def get_connection() -> Iterator[oracledb.Connection]:
    settings = get_settings()

    if not settings.app_user or not settings.app_user_password:
        raise ConfigurationError(
            "APP_USER and APP_USER_PASSWORD must be set before using the API."
        )

    connection = oracledb.connect(
        user=settings.app_user,
        password=settings.app_user_password,
        dsn=settings.oracle_dsn,
    )

    try:
        yield connection
    finally:
        connection.close()
