def build_question_tag_messages(
    *,
    title: str,
    content: str,
    existing_tags: list[dict],
) -> list[dict[str, str]]:
    tag_lines = "\n".join(
        f"- {item['tag_id']}: {item['tag_name']}"
        for item in existing_tags[:100]
    )
    if not tag_lines:
        tag_lines = "- No existing tags."

    return [
        {
            "role": "system",
            "content": (
                "你是问答社区的标签分类助手，只负责为问题选择稳定、可复用、适合公开展示的标签。"
                "请优先复用已有标签；只有已有标签完全不合适时，才创建新标签。"
                "标签应该描述问题所属领域、主题或对象，而不是描述提问方式、写作模板或临时场景。"
                "返回严格 JSON，不要包含 Markdown、解释段落或额外文本。"
            ),
        },
        {
            "role": "user",
            "content": (
                "已有标签列表：\n"
                f"{tag_lines}\n\n"
                "问题标题：\n"
                f"{title}\n\n"
                "问题内容：\n"
                f"{content}\n\n"
                "请返回以下 JSON 结构：\n"
                "{\n"
                '  "matched_tags": [{"tag_id": 100, "tag_name": "短途旅行", "confidence_score": 90}],\n'
                '  "new_tags": [{"tag_name": "宠物健康", "confidence_score": 85}],\n'
                '  "reason": "简短说明为什么这些标签贴合问题"\n'
                "}\n"
                "规则：\n"
                "1. matched_tags 和 new_tags 总数最多 3 个，宁缺毋滥。\n"
                "2. 优先选择领域标签，例如：短途旅行、宠物健康、摄影修图、个人理财、语言学习。\n"
                "3. 避免选择或创建过泛标签，例如：新手建议、入门准备清单、最小可行方案、产品优化、方案评估、日常生活结合。\n"
                "4. 避免把标题里的临时句式当作标签，例如：预算有限、长期使用、踩坑、怎么安排。\n"
                "5. 新标签必须是 2-8 个中文字的名词短语；除通用技术缩写外，不要创建英文、拼音、中英混排或带连字符的标签。\n"
                "6. 不要选择或创建低俗、成人、攻击性、无意义或不适合公开社区展示的标签。\n"
                "7. confidence_score 必须是 0-100；低于 70 的候选不要返回。\n"
                "8. 如果没有合适标签，可以返回空数组，不要强行凑满。"
            ),
        },
    ]
