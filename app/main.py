from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.api.routes import auth
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_allow_origins),
    allow_credentials="*" not in settings.cors_allow_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    if settings.content_security_policy:
        response.headers.setdefault(
            "Content-Security-Policy",
            settings.content_security_policy,
        )
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault("X-Frame-Options", "DENY")
    return response


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):  # noqa: ARG001
    return JSONResponse(
        status_code=422,
        content={
            "detail": "提交字段不符合要求，请检查必填项、长度和格式后再试。"
        },
    )


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(api_router)
