"""
Reclassify existing questions into active standard categories with AI.

The script is safe by default:
- Dry-run is the default and does not change data.
- `--apply` is required to update question.category_id.
- `--scope inactive` only fixes questions whose current category is missing or inactive.
- `--scope all` rechecks every non-deleted question.
"""

from __future__ import annotations

import argparse
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import oracledb


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.core.category_catalog import DEFAULT_CATEGORY_NAME, category_order_case_sql
from app.db.connection import get_connection
from app.repositories.log_repository import LogRepository
from app.services.ai_category_service import AICategoryService, GeneratedCategory


@dataclass(frozen=True)
class QuestionCandidate:
    question_id: int
    current_category_id: int | None
    current_category_name: str | None
    current_category_status: str | None
    title: str
    content: str
    status: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Use AI to reclassify existing questions into active categories.",
    )
    parser.add_argument(
        "--scope",
        choices=("inactive", "all"),
        default="inactive",
        help="inactive fixes missing/inactive categories; all rechecks every non-deleted question.",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write category updates to the database. Without this flag, dry-run only.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of questions to process.",
    )
    parser.add_argument(
        "--sleep-seconds",
        type=float,
        default=0.4,
        help="Pause between AI calls to avoid burst traffic.",
    )
    parser.add_argument(
        "--max-content-chars",
        type=int,
        default=2400,
        help="Maximum question content length sent to the AI classifier.",
    )
    parser.add_argument(
        "--fallback-default",
        action="store_true",
        help="When AI cannot classify an inactive-category question, use the default category.",
    )
    parser.add_argument(
        "--min-confidence",
        type=float,
        default=AICategoryService.MIN_CONFIDENCE,
        help="Minimum AI confidence required for accepting a category.",
    )
    parser.add_argument(
        "--stop-on-error",
        action="store_true",
        help="Stop immediately when one question fails.",
    )
    return parser.parse_args()


def load_active_categories(connection: oracledb.Connection) -> list[dict[str, Any]]:
    cursor = connection.cursor()
    category_order_sql = category_order_case_sql()
    cursor.execute(
        f"""
        SELECT
            category_id,
            category_name,
            description,
            status
        FROM categories
        WHERE status = 'ACTIVE'
        ORDER BY
            {category_order_sql},
            category_name,
            category_id
        """
    )
    return [
        {
            "category_id": int(row[0]),
            "category_name": row[1],
            "description": row[2],
            "status": row[3],
        }
        for row in cursor.fetchall()
    ]


def get_default_category(active_categories: list[dict[str, Any]]) -> dict[str, Any]:
    for category in active_categories:
        if category["category_name"] == DEFAULT_CATEGORY_NAME:
            return category
    return active_categories[-1]


def load_candidates(
    connection: oracledb.Connection,
    *,
    scope: str,
    limit: int | None,
    max_content_chars: int,
) -> list[QuestionCandidate]:
    where_clauses = ["q.status <> 'DELETED'"]
    binds: dict[str, Any] = {
        "content_chars": max_content_chars,
    }
    if scope == "inactive":
        where_clauses.append("(c.category_id IS NULL OR c.status <> 'ACTIVE')")
    if limit is not None:
        binds["limit_rows"] = limit

    limit_prefix = "SELECT * FROM (" if limit is not None else ""
    limit_suffix = ") WHERE ROWNUM <= :limit_rows" if limit is not None else ""

    cursor = connection.cursor()
    cursor.execute(
        f"""
        {limit_prefix}
        SELECT
            q.question_id,
            q.category_id,
            c.category_name,
            c.status AS category_status,
            q.title,
            DBMS_LOB.SUBSTR(q.content, :content_chars, 1) AS content_preview,
            q.status AS question_status
        FROM questions q
        LEFT JOIN categories c
          ON c.category_id = q.category_id
        WHERE {' AND '.join(where_clauses)}
        ORDER BY q.question_id
        {limit_suffix}
        """,
        binds,
    )
    return [
        QuestionCandidate(
            question_id=int(row[0]),
            current_category_id=int(row[1]) if row[1] is not None else None,
            current_category_name=row[2],
            current_category_status=row[3],
            title=str(row[4]),
            content=str(row[5] or ""),
            status=str(row[6]),
        )
        for row in cursor.fetchall()
    ]


def update_question_category(
    connection: oracledb.Connection,
    *,
    question_id: int,
    category_id: int,
) -> None:
    cursor = connection.cursor()
    cursor.execute(
        """
        UPDATE questions
        SET category_id = :category_id
        WHERE question_id = :question_id
        """,
        {
            "question_id": question_id,
            "category_id": category_id,
        },
    )
    if int(cursor.rowcount or 0) != 1:
        raise RuntimeError(f"Question {question_id} could not be updated.")


def log_ai_category_result(
    connection: oracledb.Connection,
    *,
    question_id: int,
    generated_category: GeneratedCategory,
) -> None:
    response_text = generated_category.response_text
    if generated_category.reason:
        response_text = (
            f"{response_text}\n\n"
            f"selected_category={generated_category.category_name}, "
            f"confidence={generated_category.confidence_score}, "
            f"reason={generated_category.reason}"
        )

    LogRepository().create_prompt_log(
        connection=connection,
        question_id=question_id,
        prompt_text=generated_category.prompt_text,
        response_text=response_text,
        token_usage=generated_category.token_usage,
        model_name=generated_category.model_name,
    )


def is_inactive_category(candidate: QuestionCandidate) -> bool:
    return candidate.current_category_id is None or candidate.current_category_status != "ACTIVE"


def main() -> int:
    args = parse_args()
    if args.limit is not None and args.limit <= 0:
        raise ValueError("--limit must be greater than 0.")
    if args.max_content_chars <= 0 or args.max_content_chars > 4000:
        raise ValueError("--max-content-chars must be between 1 and 4000.")
    if args.sleep_seconds < 0:
        raise ValueError("--sleep-seconds must not be negative.")
    if args.min_confidence < 0 or args.min_confidence > 100:
        raise ValueError("--min-confidence must be between 0 and 100.")

    ai_category_service = AICategoryService()
    ai_category_service.MIN_CONFIDENCE = args.min_confidence

    with get_connection() as connection:
        active_categories = load_active_categories(connection)
        if not active_categories:
            raise RuntimeError("No active categories found.")

        default_category = get_default_category(active_categories)
        candidates = load_candidates(
            connection,
            scope=args.scope,
            limit=args.limit,
            max_content_chars=args.max_content_chars,
        )
        print(
            f"Mode={'APPLY' if args.apply else 'DRY-RUN'}, "
            f"scope={args.scope}, candidates={len(candidates)}, "
            f"default={default_category['category_name']}, "
            f"min_confidence={args.min_confidence:g}"
        )

        updated_count = 0
        skipped_count = 0
        failed_count = 0

        for index, candidate in enumerate(candidates, start=1):
            try:
                generated_category = ai_category_service.classify_question(
                    title=candidate.title,
                    content=candidate.content,
                    active_categories=active_categories,
                )

                target_category_id: int | None = None
                target_category_name: str | None = None
                reason = ""
                confidence = 0.0

                if generated_category is not None:
                    target_category_id = generated_category.category_id
                    target_category_name = generated_category.category_name
                    reason = generated_category.reason
                    confidence = generated_category.confidence_score
                elif args.fallback_default and is_inactive_category(candidate):
                    target_category_id = int(default_category["category_id"])
                    target_category_name = str(default_category["category_name"])
                    reason = "AI could not classify; fallback default category used."

                if target_category_id is None:
                    skipped_count += 1
                    print(
                        f"[{index}/{len(candidates)}] SKIP "
                        f"question_id={candidate.question_id} "
                        f"old={candidate.current_category_name} "
                        "reason=AI returned no confident active category"
                    )
                    continue

                changed = target_category_id != candidate.current_category_id
                action = "UPDATE" if changed else "KEEP"
                print(
                    f"[{index}/{len(candidates)}] {action} "
                    f"question_id={candidate.question_id} "
                    f"old={candidate.current_category_name} "
                    f"new={target_category_name} "
                    f"confidence={confidence:.0f} "
                    f"reason={reason[:90]}"
                )

                if args.apply and changed:
                    update_question_category(
                        connection,
                        question_id=candidate.question_id,
                        category_id=target_category_id,
                    )
                    if generated_category is not None:
                        log_ai_category_result(
                            connection,
                            question_id=candidate.question_id,
                            generated_category=generated_category,
                        )
                    connection.commit()
                    updated_count += 1
                elif changed:
                    updated_count += 1

                if args.sleep_seconds > 0 and index < len(candidates):
                    time.sleep(args.sleep_seconds)
            except Exception as exc:  # noqa: BLE001
                failed_count += 1
                connection.rollback()
                print(
                    f"[{index}/{len(candidates)}] ERROR "
                    f"question_id={candidate.question_id} {type(exc).__name__}: {exc}"
                )
                if args.stop_on_error:
                    raise

        print(
            f"Summary: changed_or_would_change={updated_count}, "
            f"skipped={skipped_count}, failed={failed_count}, "
            f"written={'yes' if args.apply else 'no'}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
