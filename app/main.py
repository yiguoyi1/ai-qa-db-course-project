from fastapi import FastAPI

from app.api.router import api_router
from app.core.settings import get_settings


settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Minimal single-turn AI QA loop backed by Oracle 26ai and DeepSeek.",
)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(api_router)
