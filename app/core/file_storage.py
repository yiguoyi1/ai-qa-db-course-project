from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4


REPO_ROOT = Path(__file__).resolve().parents[2]
UPLOADS_ROOT = REPO_ROOT / "uploads"
AVATAR_UPLOAD_DIR = UPLOADS_ROOT / "avatars"
QUESTION_UPLOAD_DIR = UPLOADS_ROOT / "questions"
ANSWER_UPLOAD_DIR = UPLOADS_ROOT / "answers"


@dataclass(frozen=True)
class StoredFile:
    file_name: str
    storage_path: str
    public_url: str


def ensure_upload_directories() -> None:
    UPLOADS_ROOT.mkdir(parents=True, exist_ok=True)
    AVATAR_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    QUESTION_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    ANSWER_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def get_uploads_root() -> Path:
    ensure_upload_directories()
    return UPLOADS_ROOT


def save_avatar_bytes(*, content: bytes, file_ext: str) -> StoredFile:
    return _save_media_bytes(
        content=content,
        file_ext=file_ext,
        target_dir=AVATAR_UPLOAD_DIR,
        public_prefix="/uploads/avatars",
        storage_prefix=Path("uploads") / "avatars",
    )


def save_question_image_bytes(*, content: bytes, file_ext: str) -> StoredFile:
    return _save_media_bytes(
        content=content,
        file_ext=file_ext,
        target_dir=QUESTION_UPLOAD_DIR,
        public_prefix="/uploads/questions",
        storage_prefix=Path("uploads") / "questions",
    )


def save_answer_image_bytes(*, content: bytes, file_ext: str) -> StoredFile:
    return _save_media_bytes(
        content=content,
        file_ext=file_ext,
        target_dir=ANSWER_UPLOAD_DIR,
        public_prefix="/uploads/answers",
        storage_prefix=Path("uploads") / "answers",
    )


def _save_media_bytes(
    *,
    content: bytes,
    file_ext: str,
    target_dir: Path,
    public_prefix: str,
    storage_prefix: Path,
) -> StoredFile:
    ensure_upload_directories()

    normalized_ext = file_ext.lower()
    if normalized_ext and not normalized_ext.startswith("."):
        normalized_ext = f".{normalized_ext}"

    file_name = f"{uuid4().hex}{normalized_ext}"
    target_path = target_dir / file_name
    target_path.write_bytes(content)

    storage_path = storage_prefix / file_name
    public_url = f"{public_prefix}/{file_name}"

    return StoredFile(
        file_name=file_name,
        storage_path=storage_path.as_posix(),
        public_url=public_url,
    )


def delete_stored_file(storage_path: str | None) -> None:
    if not storage_path:
        return

    target_path = REPO_ROOT / storage_path
    if target_path.exists():
        try:
            target_path.unlink()
        except PermissionError:
            return
