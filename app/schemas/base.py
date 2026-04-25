from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from pydantic import BaseModel, ConfigDict


BEIJING_TZ = ZoneInfo("Asia/Shanghai")


def _serialize_api_datetime(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(BEIJING_TZ).isoformat()


class APIModel(BaseModel):
    model_config = ConfigDict(json_encoders={datetime: _serialize_api_datetime})
