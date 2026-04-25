from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.core.errors import AppError, ValidationError
from app.db.connection import get_connection
from app.integrations.llm.openai_client import LLMAnswerResult
from app.repositories.answer_repository import AnswerRepository
from app.repositories.question_repository import QuestionRepository
from app.services.ai_answer_service import AIAnswerService
from app.services.chat_service import ChatService
from app.schemas.chat import CreateFollowUpTurnRequest


@dataclass
class CheckResult:
    name: str
    passed: bool
    detail: str


class FakeClient:
    def __init__(self) -> None:
        self.calls = 0

    def generate_answer(self, messages: list[dict[str, str]]) -> LLMAnswerResult:
        self.calls += 1
        return LLMAnswerResult(
            content=f"fake-follow-up-answer-{self.calls}",
            model_name="fake-deepseek",
            token_usage=100 + self.calls,
        )


def pick_test_context() -> tuple[int, int, int]:
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT user_id
            FROM users
            WHERE status = 'ACTIVE'
            ORDER BY user_id
            FETCH FIRST 2 ROWS ONLY
            """
        )
        users = [int(row[0]) for row in cursor.fetchall()]
        if len(users) < 2:
            raise RuntimeError("至少需要两个 ACTIVE 用户才能运行多轮追问自检。")

        cursor.execute(
            """
            SELECT category_id
            FROM categories
            WHERE status = 'ACTIVE'
            ORDER BY category_id
            FETCH FIRST 1 ROWS ONLY
            """
        )
        row = cursor.fetchone()
        if row is None:
            raise RuntimeError("至少需要一个 ACTIVE 分类才能运行多轮追问自检。")

        return users[0], users[1], int(row[0])


def ensure_chat_schema_ready() -> None:
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM user_tab_columns
            WHERE table_name = 'CHAT_SESSION'
              AND column_name IN ('QUESTION_ID', 'SEED_ANSWER_ID')
            """
        )
        count = int(cursor.fetchone()[0] or 0)
        if count != 2:
            raise RuntimeError(
                "CHAT_SESSION 尚未补齐 QUESTION_ID / SEED_ANSWER_ID。"
                "请先执行 @sql/migrations/20260425_extend_chat_session_for_follow_up.sql"
            )


def build_test_data(
    *,
    user_id: int,
    category_id: int,
) -> dict[str, int]:
    question_repository = QuestionRepository()
    answer_repository = AnswerRepository()

    marker = f"[chat_self_check_{datetime.now().strftime('%Y%m%d%H%M%S')}]"

    with get_connection() as connection:
        question_id = question_repository.create_question(
            connection=connection,
            user_id=user_id,
            category_id=category_id,
            title=f"{marker} AI 多轮追问测试",
            content="请说明 Oracle Docker 容器启动后的首轮排查步骤。",
        )
        ai_answer_id = answer_repository.create_ai_answer(
            connection=connection,
            question_id=question_id,
            provider_name="DeepSeek",
            content="这是 AI 首答：先检查容器状态、健康检查、日志和监听端口。",
            model_name="fake-seed-model",
        )
        manual_answer_id = answer_repository.create_manual_answer(
            connection=connection,
            question_id=question_id,
            user_id=user_id,
            content="这是人工回答：也可以先检查 docker logs。",
        )

        other_question_id = question_repository.create_question(
            connection=connection,
            user_id=user_id,
            category_id=category_id,
            title=f"{marker} 锚点错位测试",
            content="这是为了验证 answer_id 与 question_id 锚点匹配规则。",
        )
        other_ai_answer_id = answer_repository.create_ai_answer(
            connection=connection,
            question_id=other_question_id,
            provider_name="DeepSeek",
            content="这是另一条问题下的 AI 回答。",
            model_name="fake-seed-model",
        )
        connection.commit()

    return {
        "question_id": question_id,
        "ai_answer_id": ai_answer_id,
        "manual_answer_id": manual_answer_id,
        "other_question_id": other_question_id,
        "other_ai_answer_id": other_ai_answer_id,
    }


def cleanup_test_data(
    *,
    question_id: int,
    other_question_id: int,
    session_ids: list[int],
) -> None:
    with get_connection() as connection:
        cursor = connection.cursor()
        for session_id in sorted(set(session_ids)):
            cursor.execute(
                "DELETE FROM chat_message WHERE session_id = :session_id",
                {"session_id": session_id},
            )
            cursor.execute(
                "DELETE FROM chat_session WHERE session_id = :session_id",
                {"session_id": session_id},
            )

        for qid in [question_id, other_question_id]:
            cursor.execute(
                "DELETE FROM ai_prompt_log WHERE question_id = :question_id",
                {"question_id": qid},
            )
            cursor.execute(
                "DELETE FROM answers WHERE question_id = :question_id",
                {"question_id": qid},
            )
            cursor.execute(
                "DELETE FROM questions WHERE question_id = :question_id",
                {"question_id": qid},
            )
        connection.commit()


def expect_validation_error(
    *,
    name: str,
    fn,
    contains: str,
) -> CheckResult:
    try:
        fn()
    except ValidationError as exc:
        if contains in exc.message:
            return CheckResult(name=name, passed=True, detail=exc.message)
        return CheckResult(
            name=name,
            passed=False,
            detail=f"收到 ValidationError，但文案不匹配：{exc.message}",
        )
    except AppError as exc:
        return CheckResult(
            name=name,
            passed=False,
            detail=f"收到非预期 AppError：{exc.message}",
        )
    except Exception as exc:  # noqa: BLE001
        return CheckResult(name=name, passed=False, detail=f"收到非预期异常：{exc}")

    return CheckResult(name=name, passed=False, detail="未抛出预期的 ValidationError。")


def run_self_check() -> list[CheckResult]:
    ensure_chat_schema_ready()

    primary_user_id, secondary_user_id, category_id = pick_test_context()
    fake_ai_service = AIAnswerService(client=FakeClient())
    chat_service = ChatService(ai_answer_service=fake_ai_service)
    data = build_test_data(user_id=primary_user_id, category_id=category_id)
    session_ids: list[int] = []
    results: list[CheckResult] = []

    try:
        first = chat_service.create_follow_up_turn(
            question_id=data["question_id"],
            answer_id=data["ai_answer_id"],
            current_user_id=primary_user_id,
            payload=CreateFollowUpTurnRequest(content="如果 health 一直不变成 healthy，我先查什么？"),
        )
        session_id = first.session.session_id
        session_ids.append(session_id)
        results.append(
            CheckResult(
                name="ai_answer_can_start_session",
                passed=len(first.messages) == 2 and first.messages[-1].sender_type == "AI",
                detail=f"session_id={session_id}, message_count={len(first.messages)}",
            )
        )

        second = chat_service.create_follow_up_turn(
            question_id=data["question_id"],
            answer_id=data["ai_answer_id"],
            current_user_id=primary_user_id,
            payload=CreateFollowUpTurnRequest(
                session_id=session_id,
                content="那数据库用户和 PDB 这块还要注意什么？",
            ),
        )
        results.append(
            CheckResult(
                name="session_can_continue",
                passed=len(second.messages) == 4 and second.messages[-1].content == "fake-follow-up-answer-2",
                detail=f"message_count={len(second.messages)}",
            )
        )

        listed = chat_service.list_sessions_by_anchor(
            question_id=data["question_id"],
            answer_id=data["ai_answer_id"],
            current_user_id=primary_user_id,
        )
        results.append(
            CheckResult(
                name="list_sessions_by_anchor",
                passed=listed.item_count == 1 and listed.items[0].session_id == session_id,
                detail=f"item_count={listed.item_count}",
            )
        )

        detail = chat_service.get_session_detail(
            session_id=session_id,
            current_user_id=primary_user_id,
        )
        results.append(
            CheckResult(
                name="get_session_detail",
                passed=len(detail.messages) == 4 and detail.messages[-1].sender_type == "AI",
                detail=f"message_count={len(detail.messages)}",
            )
        )

        foreign_listed = chat_service.list_sessions_by_anchor(
            question_id=data["question_id"],
            answer_id=data["ai_answer_id"],
            current_user_id=secondary_user_id,
        )
        results.append(
            CheckResult(
                name="allow_foreign_session_list",
                passed=foreign_listed.item_count == 1 and foreign_listed.items[0].session_id == session_id,
                detail=f"item_count={foreign_listed.item_count}",
            )
        )

        foreign_detail = chat_service.get_session_detail(
            session_id=session_id,
            current_user_id=secondary_user_id,
        )
        results.append(
            CheckResult(
                name="allow_foreign_session_detail",
                passed=len(foreign_detail.messages) == 4 and foreign_detail.session.session_id == session_id,
                detail=f"message_count={len(foreign_detail.messages)}",
            )
        )

        results.append(
            expect_validation_error(
                name="reject_manual_answer_seed",
                fn=lambda: chat_service.create_follow_up_turn(
                    question_id=data["question_id"],
                    answer_id=data["manual_answer_id"],
                    current_user_id=primary_user_id,
                    payload=CreateFollowUpTurnRequest(content="人工回答不能被拿来继续追问"),
                ),
                contains="仅支持基于 AI 回答发起",
            )
        )

        results.append(
            expect_validation_error(
                name="reject_question_answer_mismatch",
                fn=lambda: chat_service.create_follow_up_turn(
                    question_id=data["question_id"],
                    answer_id=data["other_ai_answer_id"],
                    current_user_id=primary_user_id,
                    payload=CreateFollowUpTurnRequest(content="错位锚点不应该通过"),
                ),
                contains="does not belong",
            )
        )

        results.append(
            expect_validation_error(
                name="reject_foreign_session_continue",
                fn=lambda: chat_service.create_follow_up_turn(
                    question_id=data["question_id"],
                    answer_id=data["ai_answer_id"],
                    current_user_id=secondary_user_id,
                    payload=CreateFollowUpTurnRequest(
                        session_id=session_id,
                        content="别人不能续写这个会话",
                    ),
                ),
                contains="不能续写别人的 AI 会话",
            )
        )

        results.append(
            expect_validation_error(
                name="reject_session_anchor_mismatch",
                fn=lambda: chat_service.create_follow_up_turn(
                    question_id=data["other_question_id"],
                    answer_id=data["other_ai_answer_id"],
                    current_user_id=primary_user_id,
                    payload=CreateFollowUpTurnRequest(
                        session_id=session_id,
                        content="session_id 不能被挂到其他问题和回答上",
                    ),
                ),
                contains="session_id 与当前问题或 AI 回答不匹配",
            )
        )

        with get_connection() as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                UPDATE chat_session
                SET status = 'CLOSED',
                    end_time = SYSDATE
                WHERE session_id = :session_id
                """,
                {"session_id": session_id},
            )
            connection.commit()

        results.append(
            expect_validation_error(
                name="reject_closed_session_continue",
                fn=lambda: chat_service.create_follow_up_turn(
                    question_id=data["question_id"],
                    answer_id=data["ai_answer_id"],
                    current_user_id=primary_user_id,
                    payload=CreateFollowUpTurnRequest(
                        session_id=session_id,
                        content="关闭后的会话不能继续追问",
                    ),
                ),
                contains="当前 AI 会话已关闭",
            )
        )
    finally:
        cleanup_test_data(
            question_id=data["question_id"],
            other_question_id=data["other_question_id"],
            session_ids=session_ids,
        )

    return results


def main() -> int:
    try:
        results = run_self_check()
    except Exception as exc:  # noqa: BLE001
        print(
            json.dumps(
                {
                    "success": False,
                    "error": str(exc),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 1

    success = all(item.passed for item in results)
    print(
        json.dumps(
            {
                "success": success,
                "results": [
                    {
                        "name": item.name,
                        "passed": item.passed,
                        "detail": item.detail,
                    }
                    for item in results
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
