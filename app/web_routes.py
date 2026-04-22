from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse, RedirectResponse


WEB_DIR = Path(__file__).resolve().parent / "web"

web_router = APIRouter(include_in_schema=False)


def _page_response(filename: str) -> FileResponse:
    return FileResponse(WEB_DIR / filename)


@web_router.get("/")
def root_page() -> RedirectResponse:
    return RedirectResponse(url="/login")


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


@web_router.get("/questions/{question_id}")
def question_detail_page(question_id: int) -> FileResponse:
    return _page_response("detail.html")


@web_router.get("/detail.html")
def legacy_question_detail_page() -> FileResponse:
    return _page_response("detail.html")
