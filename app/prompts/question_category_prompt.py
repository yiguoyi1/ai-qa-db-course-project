def build_question_category_messages(
    *,
    title: str,
    content: str,
    active_categories: list[dict],
) -> list[dict[str, str]]:
    category_lines = "\n".join(
        f"- {item['category_id']}: {item['category_name']} - {item.get('description') or ''}"
        for item in active_categories
    )
    if not category_lines:
        category_lines = "- No active categories."

    return [
        {
            "role": "system",
            "content": (
                "你是问答社区的问题分类助手，只能从给定的已有分类中选择一个最合适的分类。"
                "分类用于社区导航，必须稳定、克制、可复用。"
                "不要创建新分类，不要输出不在候选列表中的分类。"
                "返回严格 JSON，不要包含 Markdown、解释段落或额外文本。"
            ),
        },
        {
            "role": "user",
            "content": (
                "可选分类列表：\n"
                f"{category_lines}\n\n"
                "问题标题：\n"
                f"{title}\n\n"
                "问题内容：\n"
                f"{content}\n\n"
                "请返回以下 JSON 结构：\n"
                "{\n"
                '  "category_id": 7,\n'
                '  "category_name": "旅行户外",\n'
                '  "confidence_score": 92,\n'
                '  "reason": "问题主要讨论旅行路线、行程安排和出行体验"\n'
                "}\n"
                "规则：\n"
                "1. 必须只选择一个已有分类，category_id 必须来自可选分类列表。\n"
                "2. 优先根据问题的真实主题分类，不要被临时句式影响。\n"
                "3. 如果问题跨多个领域，选择用户最主要想解决的问题所属领域。\n"
                "4. 如果确实无法判断，选择“其他问题”。\n"
                "5. confidence_score 必须是 0-100；不确定时给低分，不要假装确定。"
            ),
        },
    ]
