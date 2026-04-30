from pathlib import Path

from fastapi import APIRouter
from fastapi import HTTPException
from fastapi.responses import FileResponse


WEB_DIR = Path(__file__).resolve().parent / "web"
PROMO_DIR = WEB_DIR.parent.parent / "promo"
ALLOWED_PROMO_FILES = {
    "ai-qa-community-enterprise-saas-promo.mp4",
    "ai-qa-community-enterprise-saas-promo-poster.png",
    "ai-qa-community-logo-aiq.png",
}

web_router = APIRouter(include_in_schema=False)


def _page_response(filename: str) -> FileResponse:
    return FileResponse(
        WEB_DIR / filename,
        headers={
            "Cache-Control": "no-store, max-age=0",
            "Pragma": "no-cache",
        },
    )


@web_router.get("/promo/{filename}")
def promo_asset(filename: str) -> FileResponse:
    if filename not in ALLOWED_PROMO_FILES:
        raise HTTPException(status_code=404, detail="Promo asset not found")

    file_path = PROMO_DIR / filename
    if not file_path.is_file():
        raise HTTPException(status_code=404, detail="Promo asset not found")

    return FileResponse(
        file_path,
        headers={
            "Cache-Control": "no-cache, max-age=0",
        },
    )


@web_router.get("/")
@web_router.get("/index.html")
def landing_page() -> FileResponse:
    return _page_response("index.html")


@web_router.get("/login")
@web_router.get("/login.html")
def login_page() -> FileResponse:
    return _page_response("login.html")


@web_router.get("/home")
@web_router.get("/home.html")
def home_page() -> FileResponse:
    return _page_response("home.html")


@web_router.get("/me")
@web_router.get("/me.html")
def profile_page() -> FileResponse:
    return _page_response("profile.html")


@web_router.get("/admin")
@web_router.get("/admin.html")
def admin_page() -> FileResponse:
    return _page_response("admin.html")


@web_router.get("/questions/{question_id}")
def question_detail_page(question_id: int) -> FileResponse:
    return _page_response("detail.html")


@web_router.get("/detail.html")
def legacy_question_detail_page() -> FileResponse:
    return _page_response("detail.html")
