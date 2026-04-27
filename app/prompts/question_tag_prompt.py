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
                "You classify question tags for a Q&A community. "
                "Return strict JSON only. Do not include markdown. "
                "Prefer matching existing tags. Create new tags only when none are suitable."
            ),
        },
        {
            "role": "user",
            "content": (
                "Existing tags:\n"
                f"{tag_lines}\n\n"
                "Question title:\n"
                f"{title}\n\n"
                "Question content:\n"
                f"{content}\n\n"
                "Return JSON with this schema:\n"
                "{\n"
                '  "matched_tags": [{"tag_id": 1, "tag_name": "oracle", "confidence_score": 90}],\n'
                '  "new_tags": [{"tag_name": "oracle-listener", "confidence_score": 85}],\n'
                '  "reason": "short reason"\n'
                "}\n"
                "Rules: choose at most 3 total tags; confidence_score must be 0-100; "
                "new tag names must be concise, lowercase when English, and no longer than 50 characters."
            ),
        },
    ]
