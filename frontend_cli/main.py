import argparse
import sys
from typing import Callable

from frontend_cli.api_client import APIClient, APIClientError
from frontend_cli.config import get_cli_settings
from frontend_cli.render import (
    print_comment_tree,
    print_json,
    print_profiles,
    print_question_detail,
    print_question_list,
    print_recommendations,
)


Handler = Callable[[argparse.Namespace, APIClient], None]


def _prompt_int(prompt: str, *, required: bool = True, default: int | None = None) -> int | None:
    while True:
        suffix = f" [{default}]" if default is not None else ""
        raw = input(f"{prompt}{suffix}: ").strip()
        if not raw:
            if default is not None:
                return default
            if not required:
                return None
            print("请输入数字。")
            continue
        try:
            return int(raw)
        except ValueError:
            print("请输入有效整数。")


def _prompt_float(
    prompt: str,
    *,
    required: bool = True,
    default: float | None = None,
) -> float | None:
    while True:
        suffix = f" [{default}]" if default is not None else ""
        raw = input(f"{prompt}{suffix}: ").strip()
        if not raw:
            if default is not None:
                return default
            if not required:
                return None
            print("请输入数字。")
            continue
        try:
            return float(raw)
        except ValueError:
            print("请输入有效数字。")


def _prompt_text(
    prompt: str,
    *,
    required: bool = True,
    default: str | None = None,
) -> str | None:
    suffix = f" [{default}]" if default is not None else ""
    while True:
        raw = input(f"{prompt}{suffix}: ").strip()
        if raw:
            return raw
        if default is not None:
            return default
        if not required:
            return None
        print("该项不能为空。")


def _prompt_tag_ids() -> list[int]:
    raw = input("tag_ids（多个用空格分隔，可留空）: ").strip()
    if not raw:
        return []
    values: list[int] = []
    for part in raw.split():
        try:
            values.append(int(part))
        except ValueError:
            print(f"忽略非法 tag_id: {part}")
    return values


def _prompt_yes_no(prompt: str, *, default: bool = False) -> bool:
    hint = "Y/n" if default else "y/N"
    raw = input(f"{prompt} [{hint}]: ").strip().lower()
    if not raw:
        return default
    return raw in {"y", "yes"}


def _run_detail_quick_actions(client: APIClient, question_id: int) -> None:
    while True:
        print()
        print("详情快捷操作")
        print("1. 记录浏览")
        print("2. 收藏问题")
        print("3. 取消收藏")
        print("4. 提交回答反馈")
        print("5. 发布人工回答")
        print("0. 返回主菜单")
        quick_choice = input("请选择操作编号: ").strip()

        try:
            if quick_choice == "0":
                return
            if quick_choice == "1":
                handle_questions_browse(
                    argparse.Namespace(
                        question_id=question_id,
                        user_id=_prompt_int("user_id"),
                        duration=_prompt_int("停留时长（秒）", default=0),
                        click_depth=_prompt_int("点击深度", default=1),
                    ),
                    client,
                )
            elif quick_choice == "2":
                handle_favorites_add(
                    argparse.Namespace(
                        question_id=question_id,
                        user_id=_prompt_int("user_id"),
                    ),
                    client,
                )
            elif quick_choice == "3":
                handle_favorites_remove(
                    argparse.Namespace(
                        question_id=question_id,
                        user_id=_prompt_int("user_id"),
                    ),
                    client,
                )
            elif quick_choice == "4":
                answer_id = _prompt_int("answer_id")
                handle_feedback_save(
                    argparse.Namespace(
                        answer_id=answer_id,
                        user_id=_prompt_int("user_id"),
                        is_like="Y" if _prompt_yes_no("是否点赞", default=True) else "N",
                        rating=_prompt_float("评分（0-5，可留空）", required=False),
                        comment_text=_prompt_text("评论（可留空）", required=False),
                    ),
                    client,
                )
            elif quick_choice == "5":
                handle_questions_answer(
                    argparse.Namespace(
                        question_id=question_id,
                        user_id=_prompt_int("user_id"),
                        content=_prompt_text("回答内容"),
                        confidence_score=_prompt_float("confidence_score（可留空）", required=False),
                    ),
                    client,
                )
            else:
                print("无效编号，请重新输入。")
        except APIClientError as exc:
            print(f"API error ({exc.status_code}): {exc.message}", file=sys.stderr)
        except KeyboardInterrupt:
            print("\n已取消当前快捷操作。")


def print_menu() -> None:
    print()
    print("=== AI QA CLI 菜单 ===")
    print("1. 健康检查")
    print("2. 查看分类")
    print("3. 查看标签")
    print("4. 问题列表")
    print("5. 问题详情")
    print("6. 提问并生成 AI 回答")
    print("7. 发布人工回答")
    print("8. 记录浏览")
    print("9. 收藏问题")
    print("10. 取消收藏")
    print("11. 提交/更新回答反馈")
    print("12. 搜索问题")
    print("13. 重建用户画像")
    print("14. 生成推荐")
    print("15. 查看推荐")
    print("0. 退出")
    print()


def handle_health(_: argparse.Namespace, client: APIClient) -> None:
    print_json(client.get("/health"))


def handle_auth_register(args: argparse.Namespace, client: APIClient) -> None:
    print_json(
        client.post(
            "/api/auth/register",
            payload={
                "username": args.username,
                "password": args.password,
                "nickname": args.nickname,
            },
        )
    )


def handle_auth_login(args: argparse.Namespace, client: APIClient) -> None:
    print_json(
        client.post(
            "/api/auth/login",
            payload={
                "username": args.username,
                "password": args.password,
            },
        )
    )


def handle_categories(_: argparse.Namespace, client: APIClient) -> None:
    print_json(client.get("/api/categories"))


def handle_tags(_: argparse.Namespace, client: APIClient) -> None:
    print_json(client.get("/api/tags"))


def handle_questions_list(args: argparse.Namespace, client: APIClient) -> None:
    data = client.get(
        "/api/questions",
        params={
            "page": args.page,
            "page_size": args.page_size,
            "category_id": args.category_id,
            "tag_id": args.tag_id,
            "status": args.status,
        },
    )
    print_question_list(data)


def handle_questions_detail(args: argparse.Namespace, client: APIClient) -> None:
    print_question_detail(client.get(f"/api/questions/{args.question_id}"))


def handle_questions_ask(args: argparse.Namespace, client: APIClient) -> None:
    data = client.post(
        "/api/questions/ask",
        payload={
            "user_id": args.user_id,
            "category_id": args.category_id,
            "title": args.title,
            "content": args.content,
            "tag_ids": args.tag_ids or [],
        },
    )
    print_question_detail(data)


def handle_questions_answer(args: argparse.Namespace, client: APIClient) -> None:
    data = client.post(
        f"/api/questions/{args.question_id}/answers",
        payload={
            "user_id": args.user_id,
            "content": args.content,
            "confidence_score": args.confidence_score,
        },
    )
    print_question_detail(data)


def handle_questions_browse(args: argparse.Namespace, client: APIClient) -> None:
    print_json(
        client.post(
            f"/api/questions/{args.question_id}/browse",
            payload={
                "user_id": args.user_id,
                "duration": args.duration,
                "click_depth": args.click_depth,
            },
        )
    )


def handle_favorites_add(args: argparse.Namespace, client: APIClient) -> None:
    print_json(
        client.post(
            f"/api/questions/{args.question_id}/favorite",
            payload={"user_id": args.user_id},
        )
    )


def handle_favorites_remove(args: argparse.Namespace, client: APIClient) -> None:
    print_json(
        client.delete(
            f"/api/questions/{args.question_id}/favorite",
            params={"user_id": args.user_id},
        )
    )


def handle_feedback_save(args: argparse.Namespace, client: APIClient) -> None:
    print_json(
        client.post(
            f"/api/answers/{args.answer_id}/feedback",
            payload={
                "user_id": args.user_id,
                "is_like": args.is_like,
                "rating": args.rating,
                "comment_text": args.comment_text,
            },
        )
    )


def handle_comments_list(args: argparse.Namespace, client: APIClient) -> None:
    print_comment_tree(client.get(f"/api/answers/{args.answer_id}/comments"))


def handle_comments_add(args: argparse.Namespace, client: APIClient) -> None:
    print_json(
        client.post(
            f"/api/answers/{args.answer_id}/comments",
            payload={
                "user_id": args.user_id,
                "content": args.content,
                "parent_comment_id": args.parent_comment_id,
            },
        )
    )


def handle_comments_delete(args: argparse.Namespace, client: APIClient) -> None:
    print_json(
        client.delete(
            f"/api/comments/{args.comment_id}",
            params={"user_id": args.user_id},
        )
    )


def handle_search_questions(args: argparse.Namespace, client: APIClient) -> None:
    data = client.get(
        "/api/search/questions",
        params={
            "q": args.q,
            "page": args.page,
            "page_size": args.page_size,
            "category_id": args.category_id,
            "tag_id": args.tag_id,
            "status": args.status,
        },
    )
    print_question_list(data)


def handle_profile_rebuild(args: argparse.Namespace, client: APIClient) -> None:
    print_profiles(client.post(f"/api/users/{args.user_id}/profile/rebuild"))


def handle_recommendations_generate(args: argparse.Namespace, client: APIClient) -> None:
    print_json(
        client.post(
            f"/api/users/{args.user_id}/recommendations/generate",
            params={"limit": args.limit},
        )
    )


def handle_recommendations_list(args: argparse.Namespace, client: APIClient) -> None:
    print_recommendations(
        client.get(
            f"/api/users/{args.user_id}/recommendations",
            params={"status": args.status},
        )
    )


def handle_menu(_: argparse.Namespace, client: APIClient) -> None:
    actions: dict[str, Handler] = {
        "1": handle_health,
        "2": handle_categories,
        "3": handle_tags,
    }

    while True:
        print_menu()
        choice = input("请选择功能编号: ").strip()

        if choice == "0":
            print("已退出。")
            return

        try:
            if choice in actions:
                actions[choice](argparse.Namespace(), client)
            elif choice == "4":
                args = argparse.Namespace(
                    page=_prompt_int("页码", default=1),
                    page_size=_prompt_int("每页数量", default=10),
                    category_id=_prompt_int("category_id", required=False),
                    tag_id=_prompt_int("tag_id", required=False),
                    status=_prompt_text("status", required=False, default="OPEN"),
                )
                handle_questions_list(args, client)
            elif choice == "5":
                question_id = _prompt_int("question_id")
                handle_questions_detail(
                    argparse.Namespace(question_id=question_id),
                    client,
                )
                _run_detail_quick_actions(client, question_id)
            elif choice == "6":
                args = argparse.Namespace(
                    user_id=_prompt_int("user_id"),
                    category_id=_prompt_int("category_id"),
                    title=_prompt_text("标题"),
                    content=_prompt_text("内容"),
                    tag_ids=_prompt_tag_ids(),
                )
                handle_questions_ask(args, client)
            elif choice == "7":
                args = argparse.Namespace(
                    question_id=_prompt_int("question_id"),
                    user_id=_prompt_int("user_id"),
                    content=_prompt_text("回答内容"),
                    confidence_score=_prompt_float("confidence_score（可留空）", required=False),
                )
                handle_questions_answer(args, client)
            elif choice == "8":
                args = argparse.Namespace(
                    question_id=_prompt_int("question_id"),
                    user_id=_prompt_int("user_id"),
                    duration=_prompt_int("停留时长（秒）", default=0),
                    click_depth=_prompt_int("点击深度", default=1),
                )
                handle_questions_browse(args, client)
            elif choice == "9":
                args = argparse.Namespace(
                    question_id=_prompt_int("question_id"),
                    user_id=_prompt_int("user_id"),
                )
                handle_favorites_add(args, client)
            elif choice == "10":
                args = argparse.Namespace(
                    question_id=_prompt_int("question_id"),
                    user_id=_prompt_int("user_id"),
                )
                handle_favorites_remove(args, client)
            elif choice == "11":
                args = argparse.Namespace(
                    answer_id=_prompt_int("answer_id"),
                    user_id=_prompt_int("user_id"),
                    is_like="Y" if _prompt_yes_no("是否点赞", default=True) else "N",
                    rating=_prompt_float("评分（0-5，可留空）", required=False),
                    comment_text=_prompt_text("评论（可留空）", required=False),
                )
                handle_feedback_save(args, client)
            elif choice == "12":
                args = argparse.Namespace(
                    q=_prompt_text("关键词"),
                    page=_prompt_int("页码", default=1),
                    page_size=_prompt_int("每页数量", default=10),
                    category_id=_prompt_int("category_id", required=False),
                    tag_id=_prompt_int("tag_id", required=False),
                    status=_prompt_text("status", required=False, default="OPEN"),
                )
                handle_search_questions(args, client)
            elif choice == "13":
                args = argparse.Namespace(
                    user_id=_prompt_int("user_id"),
                )
                handle_profile_rebuild(args, client)
            elif choice == "14":
                args = argparse.Namespace(
                    user_id=_prompt_int("user_id"),
                    limit=_prompt_int("推荐条数", default=10),
                )
                handle_recommendations_generate(args, client)
            elif choice == "15":
                args = argparse.Namespace(
                    user_id=_prompt_int("user_id"),
                    status=_prompt_text("status", required=False, default="ACTIVE"),
                )
                handle_recommendations_list(args, client)
            else:
                print("无效编号，请重新输入。")
        except APIClientError as exc:
            print(f"API error ({exc.status_code}): {exc.message}", file=sys.stderr)
        except KeyboardInterrupt:
            print("\n已取消当前操作。")


def _set_handler(parser: argparse.ArgumentParser, handler: Handler) -> None:
    parser.set_defaults(handler=handler)


def build_parser(
    default_base_url: str,
    default_timeout: int,
    default_access_token: str | None,
) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m frontend_cli.main",
        description="CLI frontend for the AI QA platform API.",
    )
    parser.add_argument("--base-url", default=default_base_url, help="API base URL")
    parser.add_argument(
        "--timeout",
        type=int,
        default=default_timeout,
        help="HTTP timeout in seconds",
    )
    parser.add_argument(
        "--access-token",
        default=default_access_token,
        help="Bearer token for authenticated requests",
    )
    subparsers = parser.add_subparsers(dest="command")

    health_parser = subparsers.add_parser("health", help="Call GET /health")
    _set_handler(health_parser, handle_health)

    auth_parser = subparsers.add_parser("auth", help="Authentication commands")
    auth_subparsers = auth_parser.add_subparsers(dest="auth_command")

    auth_register = auth_subparsers.add_parser("register", help="Register a new user")
    auth_register.add_argument("--username", required=True)
    auth_register.add_argument("--password", required=True)
    auth_register.add_argument("--nickname")
    _set_handler(auth_register, handle_auth_register)

    auth_login = auth_subparsers.add_parser("login", help="Login and get an access token")
    auth_login.add_argument("--username", required=True)
    auth_login.add_argument("--password", required=True)
    _set_handler(auth_login, handle_auth_login)

    categories_parser = subparsers.add_parser("categories", help="List categories")
    _set_handler(categories_parser, handle_categories)

    tags_parser = subparsers.add_parser("tags", help="List tags")
    _set_handler(tags_parser, handle_tags)

    menu_parser = subparsers.add_parser("menu", help="Interactive menu mode")
    _set_handler(menu_parser, handle_menu)

    questions_parser = subparsers.add_parser("questions", help="Question commands")
    questions_subparsers = questions_parser.add_subparsers(dest="questions_command")

    questions_list = questions_subparsers.add_parser("list", help="List questions")
    questions_list.add_argument("--page", type=int, default=1)
    questions_list.add_argument("--page-size", type=int, default=10)
    questions_list.add_argument("--category-id", type=int)
    questions_list.add_argument("--tag-id", type=int)
    questions_list.add_argument("--status", default="OPEN")
    _set_handler(questions_list, handle_questions_list)

    questions_detail = questions_subparsers.add_parser("detail", help="Get question detail")
    questions_detail.add_argument("--question-id", type=int, required=True)
    _set_handler(questions_detail, handle_questions_detail)

    questions_ask = questions_subparsers.add_parser("ask", help="Ask a new question")
    questions_ask.add_argument("--user-id", type=int, required=True)
    questions_ask.add_argument("--category-id", type=int, required=True)
    questions_ask.add_argument("--title", required=True)
    questions_ask.add_argument("--content", required=True)
    questions_ask.add_argument("--tag-ids", type=int, nargs="*")
    _set_handler(questions_ask, handle_questions_ask)

    questions_answer = questions_subparsers.add_parser(
        "answer",
        help="Create a manual answer for a question",
    )
    questions_answer.add_argument("--question-id", type=int, required=True)
    questions_answer.add_argument("--user-id", type=int, required=True)
    questions_answer.add_argument("--content", required=True)
    questions_answer.add_argument("--confidence-score", type=float)
    _set_handler(questions_answer, handle_questions_answer)

    questions_browse = questions_subparsers.add_parser(
        "browse",
        help="Record question browse history",
    )
    questions_browse.add_argument("--question-id", type=int, required=True)
    questions_browse.add_argument("--user-id", type=int, required=True)
    questions_browse.add_argument("--duration", type=int, default=0)
    questions_browse.add_argument("--click-depth", type=int, default=1)
    _set_handler(questions_browse, handle_questions_browse)

    favorites_parser = subparsers.add_parser("favorites", help="Favorite commands")
    favorites_subparsers = favorites_parser.add_subparsers(dest="favorites_command")

    favorites_add = favorites_subparsers.add_parser("add", help="Favorite a question")
    favorites_add.add_argument("--question-id", type=int, required=True)
    favorites_add.add_argument("--user-id", type=int, required=True)
    _set_handler(favorites_add, handle_favorites_add)

    favorites_remove = favorites_subparsers.add_parser("remove", help="Remove favorite")
    favorites_remove.add_argument("--question-id", type=int, required=True)
    favorites_remove.add_argument("--user-id", type=int, required=True)
    _set_handler(favorites_remove, handle_favorites_remove)

    feedback_parser = subparsers.add_parser("feedback", help="Feedback commands")
    feedback_subparsers = feedback_parser.add_subparsers(dest="feedback_command")

    feedback_save = feedback_subparsers.add_parser(
        "save",
        help="Create or update answer feedback",
    )
    feedback_save.add_argument("--answer-id", type=int, required=True)
    feedback_save.add_argument("--user-id", type=int, required=True)
    feedback_save.add_argument("--is-like", choices=["Y", "N"], required=True)
    feedback_save.add_argument("--rating", type=float)
    feedback_save.add_argument("--comment-text")
    _set_handler(feedback_save, handle_feedback_save)

    comments_parser = subparsers.add_parser("comments", help="Comment commands")
    comments_subparsers = comments_parser.add_subparsers(dest="comments_command")

    comments_list = comments_subparsers.add_parser("list", help="List comments for an answer")
    comments_list.add_argument("--answer-id", type=int, required=True)
    _set_handler(comments_list, handle_comments_list)

    comments_add = comments_subparsers.add_parser(
        "add",
        help="Create a top-level comment or reply",
    )
    comments_add.add_argument("--answer-id", type=int, required=True)
    comments_add.add_argument("--user-id", type=int, required=True)
    comments_add.add_argument("--content", required=True)
    comments_add.add_argument("--parent-comment-id", type=int)
    _set_handler(comments_add, handle_comments_add)

    comments_delete = comments_subparsers.add_parser(
        "delete",
        help="Soft delete a comment while keeping the thread",
    )
    comments_delete.add_argument("--comment-id", type=int, required=True)
    comments_delete.add_argument("--user-id", type=int, required=True)
    _set_handler(comments_delete, handle_comments_delete)

    search_parser = subparsers.add_parser("search", help="Search commands")
    search_subparsers = search_parser.add_subparsers(dest="search_command")

    search_questions = search_subparsers.add_parser("questions", help="Search questions")
    search_questions.add_argument("--q", required=True)
    search_questions.add_argument("--page", type=int, default=1)
    search_questions.add_argument("--page-size", type=int, default=10)
    search_questions.add_argument("--category-id", type=int)
    search_questions.add_argument("--tag-id", type=int)
    search_questions.add_argument("--status", default="OPEN")
    _set_handler(search_questions, handle_search_questions)

    recommendations_parser = subparsers.add_parser(
        "recommendations",
        help="Recommendation commands",
    )
    recommendations_subparsers = recommendations_parser.add_subparsers(
        dest="recommendations_command"
    )

    profile_rebuild = recommendations_subparsers.add_parser(
        "rebuild-profile",
        help="Rebuild user tag profile",
    )
    profile_rebuild.add_argument("--user-id", type=int, required=True)
    _set_handler(profile_rebuild, handle_profile_rebuild)

    recommendations_generate = recommendations_subparsers.add_parser(
        "generate",
        help="Generate recommendations",
    )
    recommendations_generate.add_argument("--user-id", type=int, required=True)
    recommendations_generate.add_argument("--limit", type=int, default=10)
    _set_handler(recommendations_generate, handle_recommendations_generate)

    recommendations_list = recommendations_subparsers.add_parser(
        "list",
        help="List recommendations",
    )
    recommendations_list.add_argument("--user-id", type=int, required=True)
    recommendations_list.add_argument("--status", default="ACTIVE")
    _set_handler(recommendations_list, handle_recommendations_list)

    return parser


def main() -> int:
    settings = get_cli_settings()
    parser = build_parser(
        settings.base_url,
        settings.timeout_seconds,
        settings.access_token,
    )
    args = parser.parse_args()

    handler: Handler | None = getattr(args, "handler", None)
    if handler is None:
        parser.print_help()
        return 1

    client = APIClient(
        base_url=args.base_url.rstrip("/"),
        timeout_seconds=args.timeout,
        access_token=args.access_token,
    )
    try:
        handler(args, client)
    except APIClientError as exc:
        print(f"API error ({exc.status_code}): {exc.message}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
