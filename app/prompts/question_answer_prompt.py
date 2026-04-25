def build_question_answer_messages(title: str, content: str) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": (
                "你是一个问答平台中的 AI 回答生成模块。"
                "你的任务是根据用户提交的问题标题和问题内容，直接回答用户真正想解决的问题。"
                "请使用简洁、准确、结构清晰的中文作答，优先给出可执行建议、明确步骤和关键注意事项。"
                "不要擅自把问题改写成“某个产品是什么”之类的介绍型回答，除非用户明确这样问。"
                "如果信息不足，请明确说明你的判断基于哪些假设。"
                "如果问题涉及数据库、Docker、Oracle、API 接入或编程实现，请尽量给出能直接落地的方案。"
            ),
        },
        {
            "role": "user",
            "content": (
                f"问题标题：{title}\n"
                f"问题内容：{content}\n"
                "请直接回答这个问题；如果适合，先给结论，再给简要步骤或说明。"
            ),
        },
    ]


def build_follow_up_messages(
    *,
    title: str,
    content: str,
    seed_answer_content: str,
    history_messages: list[dict[str, str]],
) -> list[dict[str, str]]:
    messages: list[dict[str, str]] = [
        {
            "role": "system",
            "content": (
                "你是问答社区中的 AI 连续追问助手。"
                "你需要基于原始问题、你此前给出的 AI 首答，以及当前会话历史继续回答用户追问。"
                "请保持上下文连续，不要每轮都重新写成陌生问题的首答。"
                "回答要使用中文，优先给出直接结论、补充说明和下一步建议。"
                "如果用户是在追问某个细节，就只回答该细节，不要重复整篇长答案。"
                "如果上下文信息不足，请明确指出缺少什么条件。"
            ),
        },
        {
            "role": "user",
            "content": (
                f"原始问题标题：{title}\n"
                f"原始问题内容：{content}\n"
                "请先理解这是同一个问题下的连续追问场景。"
            ),
        },
        {
            "role": "assistant",
            "content": f"我之前给出的首答是：\n{seed_answer_content}",
        },
    ]

    role_map = {
        "USER": "user",
        "AI": "assistant",
        "SYSTEM": "system",
    }
    for item in history_messages:
        sender_type = str(item.get("sender_type", "")).upper()
        role = role_map.get(sender_type)
        content_text = str(item.get("content", "")).strip()
        if role and content_text:
            messages.append({"role": role, "content": content_text})

    return messages


def render_prompt_text(messages: list[dict[str, str]]) -> str:
    return "\n\n".join(
        f"{message['role'].upper()}:\n{message['content']}" for message in messages
    )
