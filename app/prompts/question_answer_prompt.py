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


def render_prompt_text(messages: list[dict[str, str]]) -> str:
    return "\n\n".join(
        f"{message['role'].upper()}:\n{message['content']}" for message in messages
    )
