from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.router import api_router
from app.api.routes import auth
from app.core.file_storage import get_uploads_root
from app.core.settings import get_settings
from app.web_routes import web_router

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Minimal single-turn AI QA loop backed by Oracle 26ai and DeepSeek.",
)

app.include_router(web_router)
app.include_router(auth.router)
app.mount("/uploads", StaticFiles(directory=str(get_uploads_root()), check_dir=False), name="uploads")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # 允许所有域名访问（本地开发最方便）
    allow_credentials=True,
    allow_methods=["*"],      # 允许所有方法（GET, POST, 还有那个 OPTIONS!）
    allow_headers=["*"],      # 允许所有请求头
)

@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(api_router)
