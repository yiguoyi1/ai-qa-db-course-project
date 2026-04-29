"""
Govern historical tags by disabling dirty tags and merging similar tags.

The script is intentionally conservative:
- Dry-run is the default.
- `--apply` is required to write changes.
- Tags are not hard-deleted. Dirty or merged source tags are marked DISABLED.
- Question-tag relationships are migrated before a source tag is disabled.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import oracledb


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.db.connection import get_connection


DISABLE_TAG_NAMES = {
    "ntr",
    "巨乳",
    "尤物",
    "成人",
    "色情",
    "低俗",
    "约炮",
    "新手建议",
    "入门准备清单",
    "最小可行方案",
    "产品优化",
    "方案评估",
    "日常生活结合",
    "生活方式优化",
    "预算有限",
}

DISABLE_TAG_PATTERNS = (
    re.compile(r".*[-—](最小可行方案|长期使用|避坑|优化)$"),
    re.compile(r".*(相关问题|核心部分|第一版取舍)$"),
    re.compile(r"^[A-Za-z0-9+#.]+-[A-Za-z0-9+#.-]+$"),
)

MERGE_TAG_RULES = {
    "language-learning": "语言学习",
    "diy-维修": "DIY维修",
    "茶-与-冲泡": "茶与冲泡",
    "sql调优": "SQL调优",
    "api-设计": "API设计",
    "ai-辅助讨论": "AI辅助讨论",
    "ui-ux-design": "UI设计",
    "question-form-design": "提问表单设计",
    "api-call-reliability": "接口稳定性",
    "exception-handling": "异常处理",
    "hard-delete": "硬删除",
    "cli-测试": "CLI测试",
    "短途旅行优化": "短途旅行",
    "短途旅行-避坑": "短途旅行",
    "徒步优化": "周末徒步",
    "骑行优化": "城市骑行",
    "露营装备优化": "露营装备",
    "播客收听优化": "播客收听",
    "阅读技巧": "阅读写作",
    "写作优化": "阅读写作",
    "园艺融合日常": "园艺种植",
    "团购风险规避": "社区团购",
    "最小可行方案-团购": "社区团购",
    "二手交易陷阱": "二手交易",
    "健身入门陷阱": "健身塑形",
    "游戏设备入门": "游戏设备",
    "聚会优化": "聚会筹备",
    "效率工具-最小可行方案": "效率工具",
    "效率工具-长期使用": "效率工具",
}


@dataclass(frozen=True)
class Tag:
    tag_id: int
    tag_name: str
    source: str
    status: str
    description: str | None
    question_count: int


@dataclass(frozen=True)
class MergePlan:
    source: Tag
    target_name: str
    target: Tag | None
    rename_only: bool
    duplicate_relation_count: int
    movable_relation_count: int


@dataclass(frozen=True)
class DisablePlan:
    tag: Tag
    reason: str


def normalize_lookup_name(value: str) -> str:
    return value.strip().casefold()


def load_tags(connection) -> list[Tag]:
    cursor = connection.cursor()
    cursor.execute(
        """
        SELECT
            t.tag_id,
            t.tag_name,
            t.source,
            t.status,
            t.description,
            COUNT(qt.qt_id) AS question_count
        FROM tags t
        LEFT JOIN question_tags qt
          ON qt.tag_id = t.tag_id
        GROUP BY
            t.tag_id,
            t.tag_name,
            t.source,
            t.status,
            t.description
        ORDER BY t.tag_id
        """
    )
    return [
        Tag(
            tag_id=int(row[0]),
            tag_name=str(row[1]),
            source=str(row[2]),
            status=str(row[3]),
            description=row[4],
            question_count=int(row[5]),
        )
        for row in cursor.fetchall()
    ]


def count_duplicate_relations(connection, *, source_tag_id: int, target_tag_id: int) -> int:
    cursor = connection.cursor()
    cursor.execute(
        """
        SELECT COUNT(*)
        FROM question_tags source_qt
        WHERE source_qt.tag_id = :source_tag_id
          AND EXISTS (
              SELECT 1
              FROM question_tags target_qt
              WHERE target_qt.question_id = source_qt.question_id
                AND target_qt.tag_id = :target_tag_id
          )
        """,
        {
            "source_tag_id": source_tag_id,
            "target_tag_id": target_tag_id,
        },
    )
    row = cursor.fetchone()
    return int(row[0]) if row is not None else 0


def count_movable_relations(connection, *, source_tag_id: int, target_tag_id: int) -> int:
    cursor = connection.cursor()
    cursor.execute(
        """
        SELECT COUNT(*)
        FROM question_tags source_qt
        WHERE source_qt.tag_id = :source_tag_id
          AND NOT EXISTS (
              SELECT 1
              FROM question_tags target_qt
              WHERE target_qt.question_id = source_qt.question_id
                AND target_qt.tag_id = :target_tag_id
          )
        """,
        {
            "source_tag_id": source_tag_id,
            "target_tag_id": target_tag_id,
        },
    )
    row = cursor.fetchone()
    return int(row[0]) if row is not None else 0


def should_disable_tag(tag_name: str) -> str | None:
    normalized = tag_name.strip()
    compact = normalized.casefold().replace("-", "").replace("—", "")

    for blocked_name in DISABLE_TAG_NAMES:
        if blocked_name.casefold().replace("-", "").replace("—", "") == compact:
            return "blocked-or-weak-exact-name"

    for pattern in DISABLE_TAG_PATTERNS:
        if pattern.fullmatch(normalized):
            return f"blocked-pattern:{pattern.pattern}"

    return None


def build_plans(connection) -> tuple[list[MergePlan], list[DisablePlan]]:
    tags = load_tags(connection)
    by_name = {normalize_lookup_name(tag.tag_name): tag for tag in tags}
    merge_plans: list[MergePlan] = []
    merge_source_ids: set[int] = set()

    for source_name, target_name in MERGE_TAG_RULES.items():
        source = by_name.get(normalize_lookup_name(source_name))
        if source is None:
            continue
        if source.status == "DISABLED":
            continue

        target = by_name.get(normalize_lookup_name(target_name))
        rename_only = target is not None and target.tag_id == source.tag_id
        duplicate_count = 0
        movable_count = source.question_count
        if target is not None and not rename_only:
            duplicate_count = count_duplicate_relations(
                connection,
                source_tag_id=source.tag_id,
                target_tag_id=target.tag_id,
            )
            movable_count = count_movable_relations(
                connection,
                source_tag_id=source.tag_id,
                target_tag_id=target.tag_id,
            )

        merge_plans.append(
            MergePlan(
                source=source,
                target_name=target_name,
                target=target,
                rename_only=rename_only,
                duplicate_relation_count=duplicate_count,
                movable_relation_count=movable_count,
            )
        )
        merge_source_ids.add(source.tag_id)

    disable_plans: list[DisablePlan] = []
    for tag in tags:
        if tag.status == "DISABLED" or tag.tag_id in merge_source_ids:
            continue
        reason = should_disable_tag(tag.tag_name)
        if reason is None:
            continue
        disable_plans.append(DisablePlan(tag=tag, reason=reason))

    return merge_plans, disable_plans


def ensure_target_tag(connection, target_name: str) -> int:
    cursor = connection.cursor()
    cursor.execute(
        """
        SELECT tag_id, status
        FROM tags
        WHERE LOWER(tag_name) = LOWER(:tag_name)
        FETCH FIRST 1 ROWS ONLY
        """,
        {"tag_name": target_name},
    )
    row = cursor.fetchone()
    if row is not None:
        tag_id = int(row[0])
        status = str(row[1])
        if status != "ACTIVE":
            cursor.execute(
                """
                UPDATE tags
                SET status = 'ACTIVE'
                WHERE tag_id = :tag_id
                """,
                {"tag_id": tag_id},
            )
        return tag_id

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
            'Created by historical tag governance script.'
        )
        RETURNING tag_id INTO :tag_id
        """,
        {
            "tag_name": target_name,
            "tag_id": tag_id_var,
        },
    )
    value = tag_id_var.getvalue()
    if isinstance(value, list):
        value = value[0]
    return int(value)


def merge_tag(connection, plan: MergePlan) -> None:
    if plan.rename_only:
        rename_tag(connection, tag_id=plan.source.tag_id, tag_name=plan.target_name)
        return

    target_tag_id = ensure_target_tag(connection, plan.target_name)
    source_tag_id = plan.source.tag_id
    cursor = connection.cursor()

    cursor.execute(
        """
        DELETE FROM question_tags source_qt
        WHERE source_qt.tag_id = :source_tag_id
          AND EXISTS (
              SELECT 1
              FROM question_tags target_qt
              WHERE target_qt.question_id = source_qt.question_id
                AND target_qt.tag_id = :target_tag_id
          )
        """,
        {
            "source_tag_id": source_tag_id,
            "target_tag_id": target_tag_id,
        },
    )

    cursor.execute(
        """
        UPDATE question_tags
        SET tag_id = :target_tag_id,
            source = 'ADMIN_ADJUSTED'
        WHERE tag_id = :source_tag_id
        """,
        {
            "source_tag_id": source_tag_id,
            "target_tag_id": target_tag_id,
        },
    )

    disable_tag(
        connection,
        tag_id=source_tag_id,
        note=f"Merged into {plan.target_name} by historical tag governance script.",
    )


def rename_tag(connection, *, tag_id: int, tag_name: str) -> None:
    cursor = connection.cursor()
    cursor.execute(
        """
        UPDATE tags
        SET tag_name = :tag_name,
            status = 'ACTIVE',
            description = SUBSTR(
                CASE
                    WHEN description IS NULL OR TRIM(description) = '' THEN :note
                    WHEN INSTR(description, :note) > 0 THEN description
                    ELSE description || ' ' || :note
                END,
                1,
                200
            )
        WHERE tag_id = :tag_id
        """,
        {
            "tag_id": tag_id,
            "tag_name": tag_name,
            "note": "Renamed by historical tag governance script.",
        },
    )


def disable_tag(connection, *, tag_id: int, note: str) -> None:
    cursor = connection.cursor()
    cursor.execute(
        """
        UPDATE tags
        SET status = 'DISABLED',
            description = SUBSTR(
                CASE
                    WHEN description IS NULL OR TRIM(description) = '' THEN :note
                    WHEN INSTR(description, :note) > 0 THEN description
                    ELSE description || ' ' || :note
                END,
                1,
                200
            )
        WHERE tag_id = :tag_id
        """,
        {
            "tag_id": tag_id,
            "note": note,
        },
    )


def apply_plans(
    connection,
    *,
    merge_plans: list[MergePlan],
    disable_plans: list[DisablePlan],
) -> None:
    for plan in merge_plans:
        merge_tag(connection, plan)

    for plan in disable_plans:
        disable_tag(
            connection,
            tag_id=plan.tag.tag_id,
            note=f"Disabled by historical tag governance script: {plan.reason}.",
        )


def format_tag(tag: Tag | None) -> str:
    if tag is None:
        return "new ADMIN tag"
    return f"#{tag.tag_id} {tag.tag_name} ({tag.status}, {tag.question_count} questions)"


def print_plan(merge_plans: list[MergePlan], disable_plans: list[DisablePlan]) -> None:
    print("Historical tag governance plan")
    print("=" * 36)

    print(f"\nMerge similar tags: {len(merge_plans)}")
    if not merge_plans:
        print("- No merge candidates.")
    for plan in merge_plans:
        print(
            "- "
            f"#{plan.source.tag_id} {plan.source.tag_name} "
            f"({plan.source.question_count} questions) -> {plan.target_name} "
            f"[target: {format_tag(plan.target)}; "
            f"mode={'rename' if plan.rename_only else 'merge'}; "
            f"move={plan.movable_relation_count}; "
            f"duplicate={plan.duplicate_relation_count}]"
        )

    print(f"\nDisable dirty or weak tags: {len(disable_plans)}")
    if not disable_plans:
        print("- No disable candidates.")
    for plan in disable_plans:
        print(
            "- "
            f"#{plan.tag.tag_id} {plan.tag.tag_name} "
            f"({plan.tag.source}, {plan.tag.question_count} questions) "
            f"reason={plan.reason}"
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Disable dirty historical tags and merge similar tags. "
            "Dry-run by default; use --apply to write changes."
        )
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply changes. Without this flag the script only prints a plan.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    with get_connection() as connection:
        merge_plans, disable_plans = build_plans(connection)
        print_plan(merge_plans, disable_plans)

        if not args.apply:
            print("\nDRY RUN: no database changes were written. Use --apply to apply this plan.")
            return 0

        apply_plans(
            connection,
            merge_plans=merge_plans,
            disable_plans=disable_plans,
        )
        connection.commit()
        print("\nAPPLIED: historical tag governance completed.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
