import json
from typing import Any


def print_json(data: Any) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2))


def print_question_list(data: dict[str, Any]) -> None:
    print(f"页码: {data['page']}  每页: {data['page_size']}  总数: {data['total']}")
    print("-" * 72)
    for item in data["items"]:
        tags = ", ".join(tag["tag_name"] for tag in item.get("tags", [])) or "-"
        print(
            f"[{item['question_id']}] {item['title']} | 状态={item['status']} | "
            f"浏览={item['view_count']} 收藏={item['favorite_count']} 回答={item['answer_count']}"
        )
        print(f"  category_id={item['category_id']} user_id={item['user_id']} tags={tags}")


def print_question_detail(data: dict[str, Any]) -> None:
    print(f"问题 #{data['question_id']}: {data['title']}")
    print(
        f"用户={data['user_id']} 分类={data['category_id']} 状态={data['status']} "
        f"浏览={data['view_count']} 收藏={data['favorite_count']} 回答={data['answer_count']}"
    )
    if data.get("accepted_answer_id") is not None:
        print(f"已采纳回答: {data['accepted_answer_id']}")
    print(f"提问时间: {data['ask_time']}")
    print(f"标签: {', '.join(tag['tag_name'] for tag in data.get('tags', [])) or '-'}")

    images = data.get("images", [])
    if images:
        print("配图:")
        for image in images:
            print(
                f"  [{image['media_id']}] sort={image.get('sort_order')} "
                f"{image.get('mime_type')} {image.get('public_url')}"
            )
    else:
        print("配图: -")

    print("内容:")
    print(data["content"])
    print("-" * 72)
    print("回答:")
    for answer in data.get("answers", []):
        source = answer["answer_type"]
        if answer.get("author_username"):
            source += f" by {answer['author_username']}"
        elif answer.get("provider_name"):
            source += f" via {answer['provider_name']}"
        accepted_marker = " [已采纳]" if answer.get("is_accepted") else ""
        print(
            f"[{answer['answer_id']}] source={source}{accepted_marker} "
            f"model={answer.get('model_name')} 赞={answer['like_count']} 踩={answer['dislike_count']} "
            f"评分={answer.get('avg_rating')}"
        )
        answer_images = answer.get("images", [])
        if answer_images:
            print("  images:")
            for image in answer_images:
                print(
                    f"    [{image['media_id']}] sort={image.get('sort_order')} "
                    f"{image.get('mime_type')} {image.get('public_url')}"
                )
        print(answer["content"])
        print("-" * 72)


def print_recommendations(data: dict[str, Any]) -> None:
    print(f"user_id={data['user_id']} status={data['status']} total={data['total']}")
    print("-" * 72)
    for item in data["items"]:
        question = item["question"]
        tags = ", ".join(tag["tag_name"] for tag in question.get("tags", [])) or "-"
        print(
            f"[rec:{item['rec_id']}] score={item['rec_score']} type={item['rec_type']} "
            f"source={item.get('rec_source')} question={question['question_id']}"
        )
        print(f"  标题: {question['title']}")
        print(f"  原因: {item.get('rec_reason') or '-'}")
        print(f"  标签: {tags}")


def print_profiles(data: dict[str, Any]) -> None:
    print(f"user_id={data['user_id']} item_count={data['item_count']}")
    print("-" * 72)
    for item in data["items"]:
        print(
            f"tag_id={item['tag_id']} tag_name={item['tag_name']} "
            f"weight={item['weight']} update_time={item['update_time']}"
        )


def _print_comment_node(comment: dict[str, Any], *, indent: int = 0) -> None:
    prefix = "  " * indent
    author = (
        comment.get("author_nickname")
        or comment.get("author_username")
        or f"user:{comment['user_id']}"
    )
    reply_to = comment.get("reply_to_nickname") or comment.get("reply_to_username")
    header = (
        f"{prefix}[{comment['comment_id']}] author={author} "
        f"level={comment['comment_level']} replies={comment['reply_count']} "
        f"status={comment['status']}"
    )
    if reply_to:
        header += f" reply_to={reply_to}"
    print(header)
    print(f"{prefix}{comment['content']}")
    for child in comment.get("children", []):
        _print_comment_node(child, indent=indent + 1)


def print_comment_tree(data: dict[str, Any]) -> None:
    print(f"answer_id={data['answer_id']} total={data['total']}")
    print("-" * 72)
    for item in data.get("items", []):
        _print_comment_node(item)
