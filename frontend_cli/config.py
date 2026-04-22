from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
import os

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")


@dataclass(frozen=True)
class CLISettings:
    base_url: str
    timeout_seconds: int
    access_token: str | None


@lru_cache(maxsize=1)
def get_cli_settings() -> CLISettings:
    return CLISettings(
        base_url=os.getenv("CLI_API_BASE_URL", "http://127.0.0.1:8000").rstrip("/"),
        timeout_seconds=int(os.getenv("CLI_API_TIMEOUT", "30")),
        access_token=os.getenv("CLI_ACCESS_TOKEN") or None,
    )
