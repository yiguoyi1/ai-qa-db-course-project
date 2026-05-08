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
    translated_errors = [
        {
            "loc": list(error.get("loc", ())),
            "msg": _translate_validation_error(error),
            "type": error.get("type", "value_error"),
        }
        for error in exc.errors()
    ]
    return JSONResponse(
        status_code=422,
        content={"detail": translated_errors},
    )


def _translate_validation_error(error: dict) -> str:
    loc = ".".join(str(item) for item in error.get("loc", ()))
    message = str(error.get("msg", ""))
    error_type = str(error.get("type", ""))

    if "title" in loc:
        if "missing" in error_type or "too_short" in error_type:
            return "标题不能为空。"
        if "too_long" in error_type or "200" in message:
            return "标题不能超过 200 个字符。"
        return "标题格式不正确，请检查后再提交。"

    if "content" in loc:
        if "missing" in error_type or "too_short" in error_type:
            return "正文不能为空。"
        if "too_long" in error_type or "10000" in message:
            return "正文不能超过 10000 字。"
        return "正文格式不正确，请检查后再提交。"

    if "category_id" in loc:
        return "请选择有效的问题分类。"

    if "tag_ids" in loc or "custom_tags" in loc:
        return "标签格式不正确，请重新选择或填写标签。"

    if "page_size" in loc:
        return "每页数量不符合要求。"
    if "page" in loc:
        return "页码不符合要求。"

    return "提交字段不符合要求，请检查必填项、长度和格式后再试。"


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(api_router)
