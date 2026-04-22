import os
from dataclasses import dataclass
from functools import lru_cache

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Settings:
    app_name: str
    app_env: str
    app_host: str
    app_port: int
    oracle_db_host: str
    oracle_port: int
    oracle_service_name: str
    app_user: str
    app_user_password: str
    deepseek_api_key: str
    deepseek_model: str
    deepseek_base_url: str
    jwt_secret_key: str
    jwt_algorithm: str
    jwt_access_token_expire_minutes: int

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
        app_user=os.getenv("APP_USER", ""),
        app_user_password=os.getenv("APP_USER_PASSWORD", ""),
        deepseek_api_key=os.getenv("DEEPSEEK_API_KEY", ""),
        deepseek_model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
        deepseek_base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
        jwt_secret_key=os.getenv("JWT_SECRET_KEY", "").strip(),
        jwt_algorithm=os.getenv("JWT_ALGORITHM", "HS256").strip(),
        jwt_access_token_expire_minutes=int(
            os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", str(60 * 24 * 7))
        ),
    )
