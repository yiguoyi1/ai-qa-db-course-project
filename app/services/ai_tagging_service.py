from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any

from app.integrations.llm.openai_client import DeepSeekClient
from app.prompts.question_answer_prompt import render_prompt_text
from app.prompts.question_tag_prompt import build_question_tag_messages


@dataclass
class TagCandidate:
    tag_id: int | None
    tag_name: str
    confidence_score: float
    source: str


@dataclass
class GeneratedTags:
    candidates: list[TagCandidate] = field(default_factory=list)
    reason: str = ""
    model_name: str = ""
    token_usage: int = 0
    prompt_text: str = ""
    response_text: str = ""


class AITaggingService:
    MIN_CONFIDENCE = 60.0
    MAX_TAGS = 3

    def __init__(self, client: DeepSeekClient | None = None) -> None:
        self._client = client or DeepSeekClient()

    def analyze_question_tags(
        self,
        *,
        title: str,
        content: str,
        existing_tags: list[dict[str, Any]],
    ) -> GeneratedTags:
        messages = build_question_tag_messages(
            title=title,
            content=content,
            existing_tags=existing_tags,
        )
        llm_result = self._client.generate_answer(messages)
        data = self._parse_json(llm_result.content)
        candidates = self._build_candidates(data=data, existing_tags=existing_tags)

        return GeneratedTags(
            candidates=candidates,
            reason=str(data.get("reason") or "").strip(),
            model_name=llm_result.model_name,
            token_usage=llm_result.token_usage,
            prompt_text=render_prompt_text(messages),
            response_text=llm_result.content,
        )

    def _build_candidates(
        self,
        *,
        data: dict[str, Any],
        existing_tags: list[dict[str, Any]],
    ) -> list[TagCandidate]:
        existing_by_id = {int(item["tag_id"]): item for item in existing_tags}
        candidates: list[TagCandidate] = []
        seen_names: set[str] = set()

        for item in self._safe_list(data.get("matched_tags")):
            tag_id = self._to_int(item.get("tag_id"))
            if tag_id is None or tag_id not in existing_by_id:
                continue
            confidence_score = self._normalize_confidence(item.get("confidence_score"))
            if confidence_score < self.MIN_CONFIDENCE:
                continue
            tag_name = str(existing_by_id[tag_id]["tag_name"])
            key = tag_name.casefold()
            if key in seen_names:
                continue
            seen_names.add(key)
            candidates.append(
                TagCandidate(
                    tag_id=tag_id,
                    tag_name=tag_name,
                    confidence_score=confidence_score,
                    source="AI_MATCHED",
                )
            )
            if len(candidates) >= self.MAX_TAGS:
                return candidates

        for item in self._safe_list(data.get("new_tags")):
            tag_name = self._normalize_tag_name(str(item.get("tag_name") or ""))
            if not tag_name:
                continue
            confidence_score = self._normalize_confidence(item.get("confidence_score"))
            if confidence_score < self.MIN_CONFIDENCE:
                continue
            key = tag_name.casefold()
            if key in seen_names:
                continue
            seen_names.add(key)
            candidates.append(
                TagCandidate(
                    tag_id=None,
                    tag_name=tag_name,
                    confidence_score=confidence_score,
                    source="AI_CREATED",
                )
            )
            if len(candidates) >= self.MAX_TAGS:
                break

        return candidates

    @staticmethod
    def _parse_json(content: str) -> dict[str, Any]:
        text = content.strip()
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?\s*", "", text)
            text = re.sub(r"\s*```$", "", text)
        return json.loads(text)

    @staticmethod
    def _safe_list(value: Any) -> list[dict[str, Any]]:
        if not isinstance(value, list):
            return []
        return [item for item in value if isinstance(item, dict)]

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

    @staticmethod
    def _normalize_tag_name(value: str) -> str:
        normalized = re.sub(r"\s+", "-", value.strip().lstrip("#"))
        normalized = normalized.strip("-").lower()
        if len(normalized) > 50:
            normalized = normalized[:50].strip("-")
        return normalized
