"""
Import a read-only public API snapshot into the local database for tag governance tests.

This script does not connect to the production database directly and does not write
to the public server. It only reads public HTTP API responses, then optionally writes
the snapshot into the local Oracle database configured by `.env`.

Dry-run is the default. Use `--apply` to write local test data.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlencode, urljoin
from urllib.request import Request, urlopen

import oracledb


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.db.connection import get_connection


DEFAULT_BASE_URL = "http://120.55.74.107/"
IMPORT_USERNAME = "public_snapshot_importer"
IMPORT_CATEGORY_NAME = "公网快照标签治理"
IMPORT_PASSWORD_HASH = "public-snapshot-importer-not-for-login"
MAX_TITLE_LENGTH = 200


@dataclass(frozen=True)
class PublicTag:
    tag_id: int
    tag_name: str


@dataclass(frozen=True)
class PublicQuestion:
    question_id: int
    title: str
    ask_time: datetime | None
    status: str
    view_count: int
    favorite_count: int
    answer_count: int
    tags: list[PublicTag]


@dataclass(frozen=True)
class Snapshot:
    questions: list[PublicQuestion]
    public_total: int


def request_json(base_url: str, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    url = urljoin(base_url.rstrip("/") + "/", path.lstrip("/"))
    if params:
        url = f"{url}?{urlencode(params)}"

    request = Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "ai-qa-local-snapshot-importer/1.0",
        },
        method="GET",
    )
    with urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    return parsed.replace(tzinfo=None)


def load_public_questions(
    *,
    base_url: str,
    limit: int,
    page_size: int,
) -> Snapshot:
    questions: list[PublicQuestion] = []
    page = 1
    public_total = 0

    while len(questions) < limit:
        data = request_json(
            base_url,
            "/api/questions",
            {
                "page": page,
                "page_size": min(page_size, limit - len(questions)),
            },
        )
        public_total = int(data.get("total") or public_total or 0)
        items = data.get("items") or []
        if not items:
            break

        for item in items:
            tags = [
                PublicTag(
                    tag_id=int(tag["tag_id"]),
                    tag_name=str(tag["tag_name"]).strip(),
                )
                for tag in item.get("tags", [])
                if tag.get("tag_name")
            ]
            questions.append(
                PublicQuestion(
                    question_id=int(item["question_id"]),
                    title=str(item["title"]).strip(),
                    ask_time=parse_datetime(item.get("ask_time")),
                    status=str(item.get("status") or "OPEN").strip().upper(),
                    view_count=int(item.get("view_count") or 0),
                    favorite_count=int(item.get("favorite_count") or 0),
                    answer_count=int(item.get("answer_count") or 0),
                    tags=tags,
                )
            )
            if len(questions) >= limit:
                break

        page += 1
        if public_total and len(questions) >= public_total:
            break

    return Snapshot(questions=questions, public_total=public_total)


def returning_int(value: Any) -> int:
    if isinstance(value, list):
        value = value[0]
    return int(value)


def ensure_import_user(connection: oracledb.Connection) -> int:
    cursor = connection.cursor()
    cursor.execute(
        """
        SELECT user_id
        FROM users
        WHERE username = :username
        """,
        {"username": IMPORT_USERNAME},
    )
    row = cursor.fetchone()
    if row is not None:
        return int(row[0])

    user_id_var = cursor.var(oracledb.NUMBER)
    cursor.execute(
        """
        INSERT INTO users (
            username,
            password_hash,
            nickname,
            role,
            status
        ) VALUES (
            :username,
            :password_hash,
            :nickname,
            'USER',
            'ACTIVE'
        )
        RETURNING user_id INTO :user_id
        """,
        {
            "username": IMPORT_USERNAME,
            "password_hash": IMPORT_PASSWORD_HASH,
            "nickname": "公网快照导入用户",
            "user_id": user_id_var,
        },
    )
    return returning_int(user_id_var.getvalue())


def ensure_import_category(connection: oracledb.Connection) -> int:
    cursor = connection.cursor()
    cursor.execute(
        """
        SELECT category_id
        FROM categories
        WHERE category_name = :category_name
        """,
        {"category_name": IMPORT_CATEGORY_NAME},
    )
    row = cursor.fetchone()
    if row is not None:
        return int(row[0])

    category_id_var = cursor.var(oracledb.NUMBER)
    cursor.execute(
        """
        INSERT INTO categories (
            category_name,
            description,
            status
        ) VALUES (
            :category_name,
            :description,
            'ACTIVE'
        )
        RETURNING category_id INTO :category_id
        """,
        {
            "category_name": IMPORT_CATEGORY_NAME,
            "description": "本地标签治理测试使用的公网只读快照分类。",
            "category_id": category_id_var,
        },
    )
    return returning_int(category_id_var.getvalue())


def normalize_import_title(public_question: PublicQuestion) -> str:
    prefix = f"[PUBLIC#{public_question.question_id}] "
    max_original_length = MAX_TITLE_LENGTH - len(prefix)
    return prefix + public_question.title[:max_original_length]


def ensure_tag(connection: oracledb.Connection, tag_name: str) -> int:
    cursor = connection.cursor()
    cursor.execute(
        """
        SELECT tag_id
        FROM tags
        WHERE LOWER(tag_name) = LOWER(:tag_name)
        FETCH FIRST 1 ROWS ONLY
        """,
        {"tag_name": tag_name},
    )
    row = cursor.fetchone()
    if row is not None:
        return int(row[0])

    tag_id_var = cursor.var(oracledb.NUMBER)
    cursor.execute(
        """
        INSERT INTO tags (
            tag_name,
            source,
            status,
            description
        ) VALUES (
            :tag_name,
            'ADMIN',
            'ACTIVE',
            'Imported from public API snapshot for local tag governance test.'
        )
        RETURNING tag_id INTO :tag_id
        """,
        {
            "tag_name": tag_name,
            "tag_id": tag_id_var,
        },
    )
    return returning_int(tag_id_var.getvalue())


def ensure_question(
    connection: oracledb.Connection,
    *,
    user_id: int,
    category_id: int,
    public_question: PublicQuestion,
) -> int:
    title = normalize_import_title(public_question)
    cursor = connection.cursor()
    cursor.execute(
        """
        SELECT question_id
        FROM questions
        WHERE user_id = :user_id
          AND title = :title
        FETCH FIRST 1 ROWS ONLY
        """,
        {
            "user_id": user_id,
            "title": title,
        },
    )
    row = cursor.fetchone()
    if row is not None:
        return int(row[0])

    question_id_var = cursor.var(oracledb.NUMBER)
    cursor.execute(
        """
        INSERT INTO questions (
            user_id,
            category_id,
            title,
            content,
            ask_time,
            status,
            view_count,
            favorite_count,
            answer_count
        ) VALUES (
            :user_id,
            :category_id,
            :title,
            :content,
            NVL(:ask_time, SYSDATE),
            :status,
            :view_count,
            :favorite_count,
            :answer_count
        )
        RETURNING question_id INTO :question_id
        """,
        {
            "user_id": user_id,
            "category_id": category_id,
            "title": title,
            "content": (
                "Imported from public API snapshot for local tag governance testing.\n"
                f"public_question_id={public_question.question_id}\n"
                f"original_title={public_question.title}"
            ),
            "ask_time": public_question.ask_time or datetime.now(),
            "status": public_question.status
            if public_question.status in {"OPEN", "RESOLVED", "CLOSED", "ARCHIVED", "DELETED"}
            else "OPEN",
            "view_count": public_question.view_count,
            "favorite_count": public_question.favorite_count,
            "answer_count": public_question.answer_count,
            "question_id": question_id_var,
        },
    )
    return returning_int(question_id_var.getvalue())


def ensure_question_tag(
    connection: oracledb.Connection,
    *,
    question_id: int,
    tag_id: int,
) -> bool:
    cursor = connection.cursor()
    cursor.execute(
        """
        SELECT 1
        FROM question_tags
        WHERE question_id = :question_id
          AND tag_id = :tag_id
        FETCH FIRST 1 ROWS ONLY
        """,
        {
            "question_id": question_id,
            "tag_id": tag_id,
        },
    )
    if cursor.fetchone() is not None:
        return False

    cursor.execute(
        """
        INSERT INTO question_tags (
            question_id,
            tag_id,
            source,
            confidence_score
        ) VALUES (
            :question_id,
            :tag_id,
            'ADMIN_ADJUSTED',
            NULL
        )
        """,
        {
            "question_id": question_id,
            "tag_id": tag_id,
        },
    )
    return True


def import_snapshot(connection: oracledb.Connection, snapshot: Snapshot) -> dict[str, int]:
    user_id = ensure_import_user(connection)
    category_id = ensure_import_category(connection)

    imported_questions = 0
    imported_tags = 0
    imported_question_tags = 0
    seen_tag_names: set[str] = set()

    for public_question in snapshot.questions:
        question_id = ensure_question(
            connection,
            user_id=user_id,
            category_id=category_id,
            public_question=public_question,
        )
        imported_questions += 1

        for public_tag in public_question.tags:
            if not public_tag.tag_name:
                continue
            if public_tag.tag_name.casefold() not in seen_tag_names:
                imported_tags += 1
                seen_tag_names.add(public_tag.tag_name.casefold())
            tag_id = ensure_tag(connection, public_tag.tag_name)
            if ensure_question_tag(connection, question_id=question_id, tag_id=tag_id):
                imported_question_tags += 1

    return {
        "questions": imported_questions,
        "unique_tags_seen": imported_tags,
        "question_tags_inserted": imported_question_tags,
    }


def print_snapshot_summary(snapshot: Snapshot) -> None:
    tag_names: set[str] = set()
    relation_count = 0
    for question in snapshot.questions:
        relation_count += len(question.tags)
        for tag in question.tags:
            tag_names.add(tag.tag_name)

    print("Public API snapshot summary")
    print("=" * 32)
    print(f"public_total={snapshot.public_total}")
    print(f"loaded_questions={len(snapshot.questions)}")
    print(f"loaded_unique_tags={len(tag_names)}")
    print(f"loaded_question_tag_relations={relation_count}")
    print("\nSample:")
    for question in snapshot.questions[:8]:
        tags = " | ".join(tag.tag_name for tag in question.tags) or "(no tags)"
        print(f"- #{question.question_id} {question.title} => {tags}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Read public question/tag data via HTTP and optionally import it into "
            "the local Oracle database for tag governance testing."
        )
    )
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--limit", type=int, default=300)
    parser.add_argument("--page-size", type=int, default=50)
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write snapshot into local Oracle. Without this flag only prints a summary.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.limit <= 0:
        raise ValueError("--limit must be greater than 0.")
    if args.page_size <= 0 or args.page_size > 50:
        raise ValueError("--page-size must be between 1 and 50.")

    snapshot = load_public_questions(
        base_url=args.base_url,
        limit=args.limit,
        page_size=args.page_size,
    )
    print_snapshot_summary(snapshot)

    if not args.apply:
        print("\nDRY RUN: no local database changes were written. Use --apply to import.")
        return 0

    with get_connection() as connection:
        stats = import_snapshot(connection, snapshot)
        connection.commit()

    print("\nAPPLIED: public snapshot imported into local Oracle.")
    for key, value in stats.items():
        print(f"{key}={value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
