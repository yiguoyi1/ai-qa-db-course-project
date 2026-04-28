import os
from dataclasses import dataclass
from functools import lru_cache

from dotenv import load_dotenv


load_dotenv()


JWT_SECRET_PLACEHOLDER = "please-set-a-strong-random-secret-per-env"
DEFAULT_CORS_ALLOW_ORIGINS = (
    "http://127.0.0.1:8000",
    "http://localhost:8000",
    "http://tauri.localhost",
    "https://tauri.localhost",
    "tauri://localhost",
)
DEFAULT_CONTENT_SECURITY_POLICY = (
    "default-src 'self'; "
    "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
    "style-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com; "
    "img-src 'self' data: blob:; "
    "font-src 'self' data:; "
    "connect-src 'self' http: https:; "
    "object-src 'none'; "
    "base-uri 'self'; "
    "frame-ancestors 'none'"
)


def _parse_csv_env(name: str, default: tuple[str, ...]) -> tuple[str, ...]:
    raw_value = os.getenv(name, "")
    values = tuple(item.strip() for item in raw_value.split(",") if item.strip())
    return values or default


def _parse_bool_env(name: str, default: bool) -> bool:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    return raw_value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    app_name: str
    app_env: str
    app_host: str
    app_port: int
    oracle_db_host: str
    oracle_port: int
    oracle_service_name: str
    oracle_pool_min: int
    oracle_pool_max: int
    oracle_pool_increment: int
    app_user: str
    app_user_password: str
    deepseek_api_key: str
    deepseek_model: str
    deepseek_base_url: str
    deepseek_timeout_seconds: float
    jwt_secret_key: str
    jwt_algorithm: str
    jwt_access_token_expire_minutes: int
    auth_login_max_failures: int
    auth_login_window_seconds: int
    cors_allow_origins: tuple[str, ...]
    content_security_policy: str
    search_use_oracle_text: bool

    @property
    def oracle_dsn(self) -> str:
        return f"{self.oracle_db_host}:{self.oracle_port}/{self.oracle_service_name}"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings(
        app_name=os.getenv("APP_NAME", "AI QA API"),
        app_env=os.getenv("APP_ENV", "dev"),
        app_host=os.getenv("APP_HOST", "0.0.0.0"),
        app_port=int(os.getenv("APP_PORT", "8000")),
        oracle_db_host=os.getenv("ORACLE_DB_HOST", "localhost"),
        oracle_port=int(os.getenv("ORACLE_PORT", "1521")),
        oracle_service_name=os.getenv("ORACLE_SERVICE_NAME", "FREEPDB1"),
        oracle_pool_min=int(os.getenv("ORACLE_POOL_MIN", "1")),
        oracle_pool_max=int(os.getenv("ORACLE_POOL_MAX", "5")),
        oracle_pool_increment=int(os.getenv("ORACLE_POOL_INCREMENT", "1")),
        app_user=os.getenv("APP_USER", ""),
        app_user_password=os.getenv("APP_USER_PASSWORD", ""),
        deepseek_api_key=os.getenv("DEEPSEEK_API_KEY", ""),
        deepseek_model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
        deepseek_base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
        deepseek_timeout_seconds=float(os.getenv("DEEPSEEK_TIMEOUT_SECONDS", "30")),
        jwt_secret_key=os.getenv("JWT_SECRET_KEY", "").strip(),
        jwt_algorithm=os.getenv("JWT_ALGORITHM", "HS256").strip(),
        jwt_access_token_expire_minutes=int(
            os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", str(60 * 24 * 7))
        ),
        auth_login_max_failures=int(os.getenv("AUTH_LOGIN_MAX_FAILURES", "5")),
        auth_login_window_seconds=int(os.getenv("AUTH_LOGIN_WINDOW_SECONDS", "300")),
        cors_allow_origins=_parse_csv_env(
            "CORS_ALLOW_ORIGINS",
            DEFAULT_CORS_ALLOW_ORIGINS,
        ),
        content_security_policy=os.getenv(
            "CONTENT_SECURITY_POLICY",
            DEFAULT_CONTENT_SECURITY_POLICY,
        ).strip(),
        search_use_oracle_text=_parse_bool_env("SEARCH_USE_ORACLE_TEXT", False),
    )
