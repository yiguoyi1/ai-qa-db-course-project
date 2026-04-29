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
    MIN_CONFIDENCE = 70.0
    MAX_TAGS = 3
    MAX_NEW_TAG_LENGTH = 8

    BLOCKED_KEYWORDS = {
        "ntr",
        "巨乳",
        "尤物",
        "成人",
        "色情",
        "低俗",
        "约炮",
    }
    WEAK_TAG_NAMES = {
        "新手建议",
        "入门准备清单",
        "最小可行方案",
        "产品优化",
        "方案评估",
        "日常生活结合",
        "生活方式优化",
        "预算有限",
        "长期使用",
        "踩坑",
        "避坑",
        "怎么安排",
    }
    WEAK_TAG_PATTERNS = (
        re.compile(r".*[-—](最小可行方案|长期使用|避坑|优化)$"),
        re.compile(r".*(相关问题|核心部分|第一版取舍)$"),
    )
    KNOWN_ACRONYMS = ("AI", "API", "CSS", "DIY", "HTTP", "SQL", "UI", "UX")

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
            if self._should_reject_tag_name(tag_name, allow_existing=True):
                continue
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
            if not tag_name or self._should_reject_tag_name(tag_name, allow_existing=False):
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

    @classmethod
    def _normalize_tag_name(cls, value: str) -> str:
        normalized = value.strip().lstrip("#").strip()
        normalized = normalized.replace("，", " ").replace("、", " ")
        normalized = normalized.replace("/", " ").replace("\\", " ")

        if cls._contains_cjk(normalized):
            normalized = re.sub(r"[\s_]+", "", normalized)
            normalized = normalized.strip("-—_ ")
        else:
            normalized = re.sub(r"\s+", "-", normalized.lower())
            normalized = normalized.strip("-")

        normalized = cls._normalize_known_acronyms(normalized)
        if len(normalized) > 50:
            normalized = normalized[:50].strip("-")
        return normalized

    @classmethod
    def _should_reject_tag_name(cls, tag_name: str, *, allow_existing: bool) -> bool:
        normalized = cls._normalize_tag_name(tag_name)
        if not normalized:
            return True

        compact = normalized.casefold().replace("-", "").replace("—", "")
        if any(keyword.casefold() in compact for keyword in cls.BLOCKED_KEYWORDS):
            return True

        if normalized in cls.WEAK_TAG_NAMES:
            return True
        if any(pattern.fullmatch(normalized) for pattern in cls.WEAK_TAG_PATTERNS):
            return True

        if allow_existing and cls._is_hyphenated_latin_phrase(normalized):
            return True

        if not allow_existing:
            if len(normalized) > cls.MAX_NEW_TAG_LENGTH:
                return True
            if re.search(r"[-—]", normalized):
                return True
            if re.search(r"[A-Za-z]", normalized) and not cls._is_allowed_latin_tag(normalized):
                return True
            if not cls._contains_cjk(normalized) and len(normalized) < 2:
                return True

        return False

    @staticmethod
    def _contains_cjk(value: str) -> bool:
        return any("\u4e00" <= char <= "\u9fff" for char in value)

    @classmethod
    def _is_allowed_latin_tag(cls, value: str) -> bool:
        if cls._contains_cjk(value):
            return True
        if re.fullmatch(r"[A-Z]{2,6}", value):
            return True
        return value.casefold() in {
            "css",
            "deepseek",
            "docker",
            "oracle",
            "sql",
        }

    @staticmethod
    def _is_hyphenated_latin_phrase(value: str) -> bool:
        return (
            "-" in value
            and re.fullmatch(r"[A-Za-z0-9+#.-]+", value) is not None
        )

    @classmethod
    def _normalize_known_acronyms(cls, value: str) -> str:
        normalized = value
        for acronym in cls.KNOWN_ACRONYMS:
            normalized = re.sub(
                rf"(?<![A-Za-z]){re.escape(acronym)}(?![A-Za-z])",
                acronym,
                normalized,
                flags=re.IGNORECASE,
            )
        return normalized
