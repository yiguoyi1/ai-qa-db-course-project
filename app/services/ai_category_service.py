from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

from app.integrations.llm.openai_client import DeepSeekClient
from app.prompts.question_answer_prompt import render_prompt_text
from app.prompts.question_category_prompt import build_question_category_messages


@dataclass
class GeneratedCategory:
    category_id: int
    category_name: str
    confidence_score: float
    reason: str
    model_name: str
    token_usage: int
    prompt_text: str
    response_text: str


class AICategoryService:
    MIN_CONFIDENCE = 70.0

    def __init__(self, client: DeepSeekClient | None = None) -> None:
        self._client = client or DeepSeekClient()

    def classify_question(
        self,
        *,
        title: str,
        content: str,
        active_categories: list[dict[str, Any]],
    ) -> GeneratedCategory | None:
        categories_by_id = {
            int(item["category_id"]): item
            for item in active_categories
        }
        if not categories_by_id:
            return None

        messages = build_question_category_messages(
            title=title,
            content=content,
            active_categories=active_categories,
        )
        llm_result = self._client.generate_answer(messages)
        data = self._parse_json(llm_result.content)
        category_id = self._to_int(data.get("category_id"))
        confidence_score = self._normalize_confidence(data.get("confidence_score"))

        if category_id is None or category_id not in categories_by_id:
            return None
        if confidence_score < self.MIN_CONFIDENCE:
            return None

        category = categories_by_id[category_id]
        return GeneratedCategory(
            category_id=category_id,
            category_name=str(category["category_name"]),
            confidence_score=confidence_score,
            reason=str(data.get("reason") or "").strip(),
            model_name=llm_result.model_name,
            token_usage=llm_result.token_usage,
            prompt_text=render_prompt_text(messages),
            response_text=llm_result.content,
        )

    @staticmethod
    def _parse_json(content: str) -> dict[str, Any]:
        text = content.strip()
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?\s*", "", text)
            text = re.sub(r"\s*```$", "", text)
        return json.loads(text)

    @staticmethod
    def _to_int(value: Any) -> int | None:
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _normalize_confidence(value: Any) -> float:
        try:
            score = float(value)
        except (TypeError, ValueError):
            return 0.0
        return max(0.0, min(100.0, score))
