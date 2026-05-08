from pathlib import Path

from fastapi import APIRouter
from fastapi import HTTPException
from fastapi.responses import FileResponse


WEB_DIR = Path(__file__).resolve().parent / "web"
PROMO_DIR = WEB_DIR.parent.parent / "promo"
DESKTOP_DOWNLOAD_DIR = WEB_DIR.parent.parent / "downloads" / "desktop"
DESKTOP_BUNDLE_DIR = WEB_DIR.parent.parent / "desktop" / "src-tauri" / "target" / "release" / "bundle"
DESKTOP_DOWNLOAD_ROOTS = (DESKTOP_DOWNLOAD_DIR, DESKTOP_BUNDLE_DIR)
ALLOWED_PROMO_FILES = {
    "ai-qa-community-enterprise-saas-promo.mp4",
    "ai-qa-community-enterprise-saas-promo-poster.png",
    "ai-qa-community-logo-aiq.png",
}
DESKTOP_DOWNLOADS = {
    "macos": {
        "patterns": ("AI QA Community_*.dmg", "dmg/AI QA Community_*.dmg"),
        "media_type": "application/x-apple-diskimage",
    },
    "mac": {
        "patterns": ("AI QA Community_*.dmg", "dmg/AI QA Community_*.dmg"),
        "media_type": "application/x-apple-diskimage",
    },
    "windows": {
        "patterns": (
            "*setup*.exe",
            "*.exe",
            "*.msi",
            "nsis/*setup*.exe",
            "nsis/*.exe",
            "msi/*.msi",
        ),
        "media_type": "application/octet-stream",
    },
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


def _latest_matching_file(patterns: tuple[str, ...]) -> Path | None:
    for root in DESKTOP_DOWNLOAD_ROOTS:
        for pattern in patterns:
            matches = [path for path in root.glob(pattern) if path.is_file()]
            if matches:
                return max(matches, key=lambda path: path.stat().st_mtime)
    return None


@web_router.get("/downloads/desktop/{platform}")
def desktop_client_download(platform: str) -> FileResponse:
    package_config = DESKTOP_DOWNLOADS.get(platform.lower())
    if package_config is None:
        raise HTTPException(status_code=404, detail="Desktop client platform not found")

    file_path = _latest_matching_file(package_config["patterns"])
    if file_path is None:
        raise HTTPException(status_code=404, detail="Desktop client package is not available")

    return FileResponse(
        file_path,
        media_type=package_config["media_type"],
        filename=file_path.name,
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
