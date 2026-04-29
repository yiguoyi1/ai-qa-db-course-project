"""
Create demo users and AI-answered questions through the public HTTP API.

This script is intentionally API-driven instead of writing directly to Oracle:
it exercises registration, login, question creation, AI answering, and auto-tagging
the same way a real client would.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import random
import re
import string
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen


DEFAULT_BASE_URL = "http://120.55.74.107/"
DEFAULT_OUTPUT_DIR = Path("seed_outputs")
DEFAULT_SEED = 20260429

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def load_env_file(path: Path) -> None:
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        if not key or key in os.environ:
            continue

        value = value.strip().strip('"').strip("'")
        os.environ[key] = value


load_env_file(PROJECT_ROOT / ".env")

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "").strip()
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat").strip()
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com").rstrip("/")
DEEPSEEK_TIMEOUT_SECONDS = float(os.getenv("DEEPSEEK_TIMEOUT_SECONDS", "30"))
DEEPSEEK_PROFILE_BATCH_SIZE = 8
STRICT_PROFILE_RETRIES = 2

LOCAL_INTEREST_LABELS = [
    "城市骑行",
    "周末徒步",
    "咖啡探店",
    "二手相机",
    "家常料理",
    "健身塑形",
    "宠物日常",
    "阅读写作",
    "乐器练习",
    "摄影修图",
    "桌游聚会",
    "智能家居",
    "个人理财",
    "效率工具",
    "周末短途旅行",
    "园艺种植",
    "手作收纳",
    "观影记录",
    "城市漫步",
    "语言学习",
    "通勤穿搭",
    "老房改造",
    "家庭收纳",
    "数码产品",
    "跑步训练",
    "游戏设备",
    "美食烘焙",
    "DIY 维修",
    "播客收听",
    "插画临摹",
    "露营装备",
    "社区团购",
    "二手交易",
    "家居清洁",
    "茶与冲泡",
]

USER_TOPIC_CODES = [
    "city",
    "home",
    "food",
    "photo",
    "fitness",
    "travel",
    "music",
    "pet",
    "art",
    "life",
    "tech",
    "career",
    "study",
    "outdoor",
    "finance",
    "reading",
    "gaming",
    "craft",
]

QUESTION_PATTERNS = [
    "第一次接触{interest}，新手应该先从哪里开始？",
    "{interest} 在预算有限时，第一版怎么取舍？",
    "{interest} 最容易踩的坑有哪些？",
    "如果想把{interest}做好，最值得先优化的是什么？",
    "{interest} 的入门准备清单应该怎么列？",
    "怎样判断一个{interest}方案适不适合长期使用？",
    "如果只能先做一个最小可行方案，{interest} 应该保留哪些核心部分？",
    "{interest} 相关问题里，哪些做法看起来省事但其实不稳？",
    "把{interest}和日常生活结合起来时，怎么安排更自然？",
    "面对{interest}，新手最容易忽略的细节是什么？",
]

PROFILE_DESCRIPTORS = [
    "上班族",
    "自由职业者",
    "城市通勤族",
    "周末活动党",
    "轻量极简派",
    "做事偏务实的人",
    "喜欢慢慢比较的人",
    "重视体验感的人",
]

PROFILE_FOCUS = [
    "习惯先看性价比",
    "喜欢一次解决主要问题",
    "会先做最小可行方案",
    "更在意长期使用的稳定性",
    "偏好清晰、简单、能落地的方法",
]

PROFILE_SCENES = [
    "平时会在下班后和周末安排时间处理这些兴趣。",
    "遇到新东西时，通常会先找一个低成本的尝试方式。",
    "更喜欢可以快速上手、当天就能验证效果的方案。",
    "如果方案太复杂，会优先找一个更轻量的替代做法。",
]

PROFILE_SYSTEM_PROMPT = """你正在为一个中文问答社区批量生成用户画像。

只输出严格 JSON 数组，不要 Markdown，不要解释，不要代码块。
数组中每个对象都必须包含以下字段：
- username: 与输入完全一致的字符串
- nickname: 与输入完全一致的字符串
- interest_domains: 3 个中文兴趣标签，彼此尽量不同，尽量生活化、具体。每个用户最多 1 个偏技术、课程或职场的标签，其他必须是生活、消费、爱好、城市、运动、创作或家庭类。
- profile_summary: 1 句中文，概括这个用户的日常身份和偏好，20 到 40 字。
- scene_hint: 1 句中文，描述这个用户常见的使用场景，20 到 40 字。

要求：
- 保持输入顺序
- 同一批次内不要重复相同的兴趣组合
- 不要让所有人都像学生、课程项目或面试准备用户
- 不要输出生硬的英文标签，除非输入用户明显偏技术
- interest_domains 必须是名词短语，不要写成句子"""

COURSE_RELATED_MARKERS = (
    "课程",
    "数据库",
    "后端",
    "前端",
    "项目",
    "面试",
    "简历",
    "算法",
    "开发",
    "编程",
    "AI",
    "Prompt",
    "Oracle",
    "SQL",
)


DOMAINS: dict[str, dict[str, list[str]]] = {
    "database": {
        "names": ["数据库", "Oracle", "SQL 调优", "数据建模"],
        "titles": [
            "Oracle 查询突然变慢应该从哪里排查？",
            "问答社区的回答表要不要拆分 AI 回答和人工回答？",
            "如何判断一个字段适合建索引还是保留全表扫描？",
            "数据库里存图片 BLOB 和存对象存储 URL 的取舍是什么？",
            "帖子软删除之后，统计视图应该怎么排除这些数据？",
            "用户收藏和浏览历史的表设计应该注意哪些一致性问题？",
            "Oracle 里 DATE 字段展示北京时间应该放在哪一层处理？",
            "如何给问题列表做一个稳定的热度排序公式？",
            "迁移脚本和全量建表脚本应该如何保持一致？",
            "约束应该放在后端校验还是数据库 CHECK 里？",
        ],
    },
    "backend": {
        "names": ["后端开发", "FastAPI", "接口设计", "服务拆分"],
        "titles": [
            "FastAPI 项目里 routes、services、repositories 怎么分层更清楚？",
            "登录态接口应该如何返回用户角色和用户 ID？",
            "批量请求接口需要做哪些限流和错误恢复设计？",
            "后端返回错误信息时，哪些内容适合暴露给前端？",
            "如何设计一个只允许作者删除自己帖子的接口？",
            "接口返回时间字段时要统一成字符串还是交给前端格式化？",
            "上传文件接口应该先读完再校验，还是边读边限制大小？",
            "服务层应该捕获数据库异常还是让路由层统一处理？",
            "一个问答社区的搜索接口应该支持哪些基础筛选？",
            "如何写一个不会和业务代码耦合太深的测试 CLI？",
        ],
    },
    "ai": {
        "names": ["AI 应用", "Prompt", "智能问答", "大模型"],
        "titles": [
            "AI 首答生成后，用户追问应该复用哪些上下文？",
            "自动打标签时，如何避免模型生成太多重复标签？",
            "问答平台里 AI 回答和人工回答应该如何区分展示？",
            "调用 DeepSeek API 时，失败重试和超时应该怎么设计？",
            "大模型生成内容如何做基础的质量记录和审计？",
            "用户不选择标签时，AI 自动标签是否应该立刻写入数据库？",
            "如何把 AI 回答做成辅助而不是替代社区讨论？",
            "Prompt 模板应该放在代码里还是数据库里？",
            "AI 追问会话是否应该允许其他用户查看？",
            "怎样判断 AI 首答是否需要展示置信度？",
        ],
    },
    "frontend": {
        "names": ["前端交互", "页面体验", "原生网页", "表单设计"],
        "titles": [
            "发布问题弹窗里，图片上传失败应该怎样提示用户？",
            "问题详情页的回答区和评论区应该如何区分层级？",
            "头像上传前预览应该注意哪些边界情况？",
            "搜索结果为空时，页面要给用户哪些下一步提示？",
            "AI 正在回答时，按钮文案怎么写更自然？",
            "首页推荐和热门问题两个列表应该如何避免视觉重复？",
            "移动端发帖表单太长时，怎么减少用户压力？",
            "前端如何展示已删除评论但保留楼中楼上下文？",
            "用户中心里提问、回答、收藏应该如何组织？",
            "图片大图预览是否应该和问题正文分离？",
        ],
    },
    "product": {
        "names": ["产品设计", "社区运营", "内容治理", "用户增长"],
        "titles": [
            "问答社区早期应该先鼓励提问还是先鼓励回答？",
            "管理员删除帖子时，是否必须填写原因？",
            "如何设计新用户首次提问的引导流程？",
            "社区里 AI 回答太多会不会影响用户之间交流？",
            "问题被采纳答案后，是否还应该允许继续回答？",
            "如何判断一个问题适合进入热门榜？",
            "用户画像推荐要不要给用户可解释的推荐理由？",
            "内容审核后台第一版应该优先做哪些能力？",
            "标签系统应该允许用户自由创建吗？",
            "如何减少重复问题但不打断用户发帖？",
        ],
    },
    "travel": {
        "names": ["城市旅行", "天津生活", "路线规划", "本地体验"],
        "titles": [
            "第一次去天津，两天一夜怎样安排比较顺？",
            "天津适合一个人慢慢逛的路线有哪些？",
            "海河夜景和五大道应该放在同一天吗？",
            "天津本地小吃怎么安排才不会一路都在排队？",
            "如果带父母去天津，行程节奏应该怎么放慢？",
            "天津雨天旅行有哪些室内备选？",
            "从天津站出发，半天时间适合逛哪里？",
            "天津有哪些适合拍照但不太拥挤的地方？",
            "周末短途旅行预算有限时应该怎么取舍？",
            "旅行攻略类问题应该怎样描述，AI 才能给更准确路线？",
        ],
    },
    "study": {
        "names": ["学习方法", "课程项目", "数据库课程", "项目答辩"],
        "titles": [
            "数据库课程设计答辩时，老师通常会问哪些表设计问题？",
            "如何向老师解释为什么要做软删除而不是物理删除？",
            "课程项目文档应该先写业务流程还是先写数据表？",
            "如何把一个问答社区项目讲得不像简单 CRUD？",
            "学习 Oracle 时，触发器和存储过程应该掌握到什么程度？",
            "项目里用了 AI API，答辩时应该如何说明边界？",
            "如何准备数据库设计里的约束和索引说明？",
            "多人协作时，迁移脚本冲突应该怎么处理？",
            "如何检查 README 是否足够让新同学跑起来？",
            "做课程设计时，什么时候该停下补文档？",
        ],
    },
    "career": {
        "names": ["职业规划", "实习准备", "简历项目", "面试复盘"],
        "titles": [
            "数据库课程项目写进简历时应该突出哪些亮点？",
            "后端实习面试里，问答社区项目可能被追问什么？",
            "如何把 AI 问答平台讲成一个完整产品而不只是接口集合？",
            "面试时被问到项目安全性，应该从哪些角度回答？",
            "学生项目需要做到多完整才适合放到简历上？",
            "如果项目用了 Oracle，简历里怎么描述更专业？",
            "如何准备一次三分钟的项目介绍？",
            "面试官问为什么不用 MySQL 时，怎么回答比较自然？",
            "项目中哪些细节最能体现工程能力？",
            "实习前需要补哪些后端基础？",
        ],
    },
}


DETAIL_FRAGMENTS = [
    "我希望答案能给出排查顺序，而不是只列概念。",
    "如果有常见坑，也请一起说明。",
    "最好能结合一个小型问答社区项目来解释。",
    "我更关心实际落地时怎么取舍。",
    "希望回答里能包含边界情况和后续优化方向。",
    "如果方案有成本或性能影响，也请说明。",
    "我想知道第一版 MVP 应该做到什么程度。",
    "请尽量用新手也能理解的方式说明。",
    "可以给一个简短示例帮助理解。",
    "请区分必须做和以后再做的部分。",
]

NICKNAME_PREFIXES = [
    "海河", "松间", "小舟", "云边", "北辰", "南窗", "青柠", "砂糖", "晨星", "远山",
    "竹影", "橙子", "月白", "槐序", "风铃", "星野", "白露", "拾光", "微澜", "木棉",
]

NICKNAME_SUFFIXES = [
    "同学", "记录员", "提问者", "观察者", "调试员", "慢行者", "学习者", "小队长", "研究员", "体验官",
]


@dataclass
class DemoUser:
    index: int
    username: str
    password: str
    nickname: str
    domains: list[str]
    user_id: int | None = None
    token: str | None = None


@dataclass
class UserProfile:
    username: str
    nickname: str
    interest_domains: list[str]
    profile_summary: str
    scene_hint: str
    source: str = "local"


def request_json(
    base_url: str,
    method: str,
    path: str,
    payload: dict[str, Any] | None = None,
    token: str | None = None,
    timeout: int = 180,
) -> dict[str, Any]:
    url = urljoin(base_url.rstrip("/") + "/", path.lstrip("/"))
    body = None
    headers = {
        "Accept": "application/json",
        "User-Agent": "ai-qa-demo-seeder/1.0 controlled-data-generation",
    }
    if payload is not None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"

    request = Request(url, data=body, headers=headers, method=method.upper())
    try:
        with urlopen(request, timeout=timeout) as response:
            text = response.read().decode("utf-8")
            return json.loads(text) if text else {}
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{method} {url} failed with HTTP {exc.code}: {detail}") from exc
    except URLError as exc:
        raise RuntimeError(f"{method} {url} failed: {exc}") from exc


def get_health(base_url: str) -> dict[str, Any]:
    return request_json(base_url, "GET", "/health")


def get_categories(base_url: str) -> list[dict[str, Any]]:
    response = request_json(base_url, "GET", "/api/categories")
    items = response.get("items", [])
    if not items:
        raise RuntimeError("No active categories returned by /api/categories.")
    return items


def safe_slug(value: str) -> str:
    allowed = string.ascii_lowercase + string.digits + "_"
    return "".join(ch for ch in value.lower() if ch in allowed)


def normalize_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def normalize_text_list(value: Any, *, max_items: int = 3) -> list[str]:
    if not isinstance(value, list):
        return []

    items: list[str] = []
    seen: set[str] = set()
    for raw_item in value:
        item = normalize_text(raw_item)
        if not item:
            continue
        key = item.casefold()
        if key in seen:
            continue
        seen.add(key)
        items.append(item)
        if len(items) >= max_items:
            break
    return items


def strip_json_code_fence(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    return cleaned.strip()


def extract_json_text(text: str) -> str:
    cleaned = strip_json_code_fence(text)
    array_start = cleaned.find("[")
    array_end = cleaned.rfind("]")
    if array_start != -1 and array_end != -1 and array_end > array_start:
        return cleaned[array_start : array_end + 1]

    object_start = cleaned.find("{")
    object_end = cleaned.rfind("}")
    if object_start != -1 and object_end != -1 and object_end > object_start:
        return cleaned[object_start : object_end + 1]

    raise RuntimeError("DeepSeek response did not contain valid JSON.")


def build_local_profile(user: DemoUser, seed: int) -> UserProfile:
    rng = random.Random(seed * 1000 + user.index)
    interests = normalize_text_list(user.domains, max_items=3)
    pool = LOCAL_INTEREST_LABELS[:]
    rng.shuffle(pool)

    while len(interests) < 3 and pool:
        candidate = pool.pop()
        if candidate.casefold() not in {item.casefold() for item in interests}:
            interests.append(candidate)

    if len(interests) < 3:
        while len(interests) < 3:
            interests.append(rng.choice(LOCAL_INTEREST_LABELS))

    profile_summary = (
        f"{rng.choice(PROFILE_DESCRIPTORS)}，"
        f"{rng.choice(PROFILE_FOCUS)}，"
        f"主要关注{interests[0]}、{interests[1]}和{interests[2]}"
    )
    scene_hint = rng.choice(PROFILE_SCENES)

    return UserProfile(
        username=user.username,
        nickname=user.nickname,
        interest_domains=interests[:3],
        profile_summary=normalize_text(profile_summary),
        scene_hint=normalize_text(scene_hint),
        source="local",
    )


def sanitize_interest_domains(value: Any, fallback: list[str], *, seed: int, user_index: int) -> list[str]:
    if not isinstance(value, list):
        return fallback[:3]

    cleaned: list[str] = []
    seen: set[str] = set()
    technical_count = 0
    rng = random.Random(seed * 1000 + user_index)

    for raw_item in value:
        item = normalize_text(raw_item)
        if not item:
            continue
        key = item.casefold()
        if key in seen:
            continue
        if any(marker.casefold() in key for marker in COURSE_RELATED_MARKERS):
            technical_count += 1
            if technical_count > 1:
                continue
        seen.add(key)
        cleaned.append(item)
        if len(cleaned) >= 3:
            return cleaned

    fallback_pool = [item for item in fallback if item.casefold() not in seen]
    rng.shuffle(fallback_pool)
    while len(cleaned) < 3 and fallback_pool:
        cleaned.append(fallback_pool.pop())

    while len(cleaned) < 3:
        candidate = rng.choice(LOCAL_INTEREST_LABELS)
        if candidate.casefold() not in {item.casefold() for item in cleaned}:
            cleaned.append(candidate)

    return cleaned[:3]


def request_deepseek_profiles(
    users: list[DemoUser],
    seed: int,
    *,
    strict: bool,
) -> dict[str, UserProfile]:
    if strict and not DEEPSEEK_API_KEY:
        raise RuntimeError("DEEPSEEK_API_KEY is required when --strict-profiles is enabled.")

    if not DEEPSEEK_API_KEY:
        return {}

    lines = [
        f"{index}. username={user.username}; nickname={user.nickname}; hint={', '.join(user.domains)}"
        for index, user in enumerate(users, start=1)
    ]
    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": [
            {"role": "system", "content": PROFILE_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    "请根据下面的输入用户生成画像。username 和 nickname 必须原样返回，"
                    "输出数组长度必须与输入用户数量一致，顺序保持一致。\n\n"
                    + "\n".join(lines)
                ),
            },
        ],
        "temperature": 0.65 if strict else 0.85,
        "max_tokens": 2400,
    }

    response = request_json(
        DEEPSEEK_BASE_URL,
        "POST",
        "chat/completions",
        payload,
        token=DEEPSEEK_API_KEY,
        timeout=int(DEEPSEEK_TIMEOUT_SECONDS),
    )
    choices = response.get("choices") or []
    if not choices:
        raise RuntimeError("DeepSeek response did not contain any choices.")

    content = normalize_text(choices[0].get("message", {}).get("content", ""))
    if not content:
        raise RuntimeError("DeepSeek response content was empty.")

    parsed = json.loads(extract_json_text(content))
    if not isinstance(parsed, list):
        raise RuntimeError("DeepSeek profile response must be a JSON array.")

    if strict and len(parsed) != len(users):
        raise RuntimeError(
            f"DeepSeek returned {len(parsed)} profile records for a batch of {len(users)} users."
        )

    profiles: dict[str, UserProfile] = {}

    if strict:
        for user, item in zip(users, parsed, strict=True):
            if not isinstance(item, dict):
                raise RuntimeError("DeepSeek profile response contains a non-object item.")

            username = normalize_text(item.get("username"))
            if username != user.username:
                raise RuntimeError(
                    f"DeepSeek returned username '{username}' but expected '{user.username}'."
                )

            nickname = normalize_text(item.get("nickname"))
            if not nickname:
                raise RuntimeError(f"DeepSeek profile for {user.username} is missing nickname.")

            interests = normalize_text_list(item.get("interest_domains"), max_items=3)
            if len(interests) != 3:
                raise RuntimeError(
                    f"DeepSeek profile for {user.username} must contain exactly 3 interest domains."
                )

            course_like_count = sum(
                1
                for interest in interests
                if any(marker.casefold() in interest.casefold() for marker in COURSE_RELATED_MARKERS)
            )
            if course_like_count > 1:
                raise RuntimeError(
                    f"DeepSeek profile for {user.username} contains too many course-like interests."
                )

            if len({interest.casefold() for interest in interests}) != 3:
                raise RuntimeError(
                    f"DeepSeek profile for {user.username} contains duplicate interest domains."
                )

            profile_summary = normalize_text(item.get("profile_summary"))
            if not profile_summary:
                raise RuntimeError(
                    f"DeepSeek profile for {user.username} is missing profile_summary."
                )

            scene_hint = normalize_text(item.get("scene_hint"))
            if not scene_hint:
                raise RuntimeError(f"DeepSeek profile for {user.username} is missing scene_hint.")

            profiles[user.username] = UserProfile(
                username=username,
                nickname=nickname,
                interest_domains=interests,
                profile_summary=profile_summary,
                scene_hint=scene_hint,
                source="deepseek",
            )

        return profiles

    user_by_name = {user.username: user for user in users}

    for item in parsed:
        if not isinstance(item, dict):
            continue

        username = normalize_text(item.get("username"))
        if username not in user_by_name:
            continue

        user = user_by_name[username]
        fallback = build_local_profile(user, seed)
        interests = sanitize_interest_domains(
            item.get("interest_domains"),
            fallback.interest_domains,
            seed=seed,
            user_index=user.index,
        )
        profile_summary = normalize_text(item.get("profile_summary")) or fallback.profile_summary
        scene_hint = normalize_text(item.get("scene_hint")) or fallback.scene_hint
        nickname = normalize_text(item.get("nickname")) or user.nickname

        profiles[username] = UserProfile(
            username=username,
            nickname=nickname,
            interest_domains=interests,
            profile_summary=profile_summary,
            scene_hint=scene_hint,
            source="deepseek",
        )

    return profiles


def build_profiles(users: list[DemoUser], seed: int, use_deepseek: bool, batch_size: int) -> dict[str, UserProfile]:
    profiles = {user.username: build_local_profile(user, seed) for user in users}

    if not use_deepseek:
        return profiles

    for start in range(0, len(users), batch_size):
        batch = users[start : start + batch_size]
        try:
            deepseek_profiles = request_deepseek_profiles(batch, seed)
        except Exception as exc:  # noqa: BLE001 - keep the batch alive with local fallback.
            print(f"[PROFILE FALLBACK] {batch[0].index:03d}-{batch[-1].index:03d}: {exc}", file=sys.stderr)
            continue

        profiles.update(deepseek_profiles)

    return profiles


def build_users(count: int, seed: int, prefix: str) -> list[DemoUser]:
    random.seed(seed)
    users: list[DemoUser] = []
    for index in range(1, count + 1):
        domains = random.sample(LOCAL_INTEREST_LABELS, k=3)
        topic_code = random.choice(USER_TOPIC_CODES)
        token = "".join(random.choices(string.ascii_lowercase + string.digits, k=5))
        username = f"{prefix}_{safe_slug(topic_code)}_{index:03d}_{token}"
        nickname = (
            f"{random.choice(NICKNAME_PREFIXES)}"
            f"{random.choice(NICKNAME_SUFFIXES)}"
            f"{index:02d}"
        )
        password = f"AiQa@{seed % 100000}_{index:03d}_{token}"
        users.append(
            DemoUser(
                index=index,
                username=username,
                password=password,
                nickname=nickname,
                domains=domains,
            )
        )
    return users


def build_profiles(
    users: list[DemoUser],
    seed: int,
    use_deepseek: bool,
    batch_size: int,
    *,
    strict_profiles: bool,
    strict_profile_retries: int,
) -> dict[str, UserProfile]:
    if strict_profiles and not DEEPSEEK_API_KEY:
        raise RuntimeError("DEEPSEEK_API_KEY must be set when --strict-profiles is enabled.")

    profiles = {} if strict_profiles else {user.username: build_local_profile(user, seed) for user in users}

    if not use_deepseek:
        return profiles

    for start in range(0, len(users), batch_size):
        batch = users[start : start + batch_size]
        if strict_profiles:
            last_error: Exception | None = None
            deepseek_profiles: dict[str, UserProfile] = {}
            for attempt in range(1, strict_profile_retries + 2):
                try:
                    deepseek_profiles = request_deepseek_profiles(batch, seed, strict=True)
                    break
                except Exception as exc:  # noqa: BLE001 - keep retrying strict batches.
                    last_error = exc
                    if attempt < strict_profile_retries + 2:
                        time.sleep(0.5 * attempt)
                        continue
                    raise
            if last_error is not None and len(deepseek_profiles) != len(batch):
                raise last_error
        else:
            try:
                deepseek_profiles = request_deepseek_profiles(batch, seed, strict=False)
            except Exception as exc:  # noqa: BLE001 - keep the batch alive with local fallback.
                print(f"[PROFILE FALLBACK] {batch[0].index:03d}-{batch[-1].index:03d}: {exc}", file=sys.stderr)
                continue

        if strict_profiles and len(deepseek_profiles) != len(batch):
            raise RuntimeError(
                f"DeepSeek returned {len(deepseek_profiles)} profiles for a batch of {len(batch)} users."
            )

        profiles.update(deepseek_profiles)

    if strict_profiles and len(profiles) != len(users):
        raise RuntimeError(
            f"DeepSeek profile generation produced {len(profiles)} profiles for {len(users)} users."
        )

    return profiles


def build_question(
    user: DemoUser,
    profile: UserProfile,
    question_index: int,
    categories: list[dict[str, Any]],
) -> dict[str, Any]:
    rng = random.Random(user.index * 1000 + question_index)
    interest = profile.interest_domains[(question_index - 1) % len(profile.interest_domains)]
    title = QUESTION_PATTERNS[(user.index + question_index - 2) % len(QUESTION_PATTERNS)].format(
        interest=interest,
    )
    category = categories[(user.index + question_index - 2) % len(categories)]
    angle = rng.choice(DETAIL_FRAGMENTS)
    content = (
        f"我最近主要在关注「{interest}」。{title}\n\n"
        f"背景：{profile.profile_summary}。{profile.scene_hint}"
        f"{angle}如果有多个方案，请按优先级说明，并指出第一步应该怎么做。"
    )
    return {
        "category_id": int(category["category_id"]),
        "interest_domain": interest,
        "title": title,
        "content": content,
        "tag_ids": [],
        "custom_tags": [],
        "auto_tag": True,
    }


def ensure_output_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def append_csv(path: Path, fieldnames: list[str], row: dict[str, Any]) -> None:
    exists = path.exists()
    with path.open("a", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        if not exists:
            writer.writeheader()
        writer.writerow(row)


def register_or_login(base_url: str, user: DemoUser) -> DemoUser:
    register_payload = {
        "username": user.username,
        "password": user.password,
        "nickname": user.nickname,
    }
    try:
        request_json(base_url, "POST", "/api/auth/register", register_payload, timeout=60)
    except RuntimeError as exc:
        error_text = str(exc).lower()
        existing_markers = (
            "already",
            "exists",
            "重复",
            "已被注册",
            "用户名已存在",
            "已存在",
        )
        if not any(marker in error_text for marker in existing_markers):
            raise

    token_response = request_json(
        base_url,
        "POST",
        "/api/auth/login",
        {"username": user.username, "password": user.password},
        timeout=60,
    )
    user.user_id = int(token_response["user_id"])
    user.token = str(token_response["access_token"])
    return user


def run(args: argparse.Namespace) -> int:
    output_dir = Path(args.output_dir)
    ensure_output_dir(output_dir)
    run_id = args.run_id or datetime.now().strftime("%Y%m%d_%H%M%S")
    accounts_path = output_dir / f"accounts_{run_id}.csv"
    questions_path = output_dir / f"questions_{run_id}.csv"
    csv_lock = threading.Lock()
    print_lock = threading.Lock()

    users = build_users(args.users, args.seed, args.username_prefix)
    profiles = build_profiles(
        users,
        seed=args.seed,
        use_deepseek=not args.local_profiles_only and not args.dry_run,
        batch_size=args.profile_batch_size,
        strict_profiles=args.strict_profiles,
        strict_profile_retries=args.strict_profile_retries,
    )
    categories = (
        [{"category_id": 1, "category_name": "DRY_RUN"}]
        if args.dry_run
        else get_categories(args.base_url)
    )

    print(f"Base URL: {args.base_url}")
    print(f"Users: {args.users}, questions/user: {args.questions_per_user}")
    print(f"Concurrency: {args.concurrency}")
    print(
        "Profile generation: "
        + (
            "DeepSeek only (strict)"
            if args.strict_profiles and not args.dry_run
            else "DeepSeek + local fallback"
            if DEEPSEEK_API_KEY and not args.local_profiles_only and not args.dry_run
            else "local only"
        )
    )
    print(f"Output accounts: {accounts_path}")
    print(f"Output questions: {questions_path}")

    if args.dry_run:
        for user in users[: min(5, len(users))]:
            profile = profiles[user.username]
            print(
                f"[DRY] {user.username} / {user.password} / {user.nickname} / "
                f"{', '.join(profile.interest_domains)} / {profile.source}"
            )
            for question_index in range(1, min(args.questions_per_user, 3) + 1):
                question = build_question(user, profile, question_index, categories)
                print(f"      - {question['title']}")
        return 0

    health = get_health(args.base_url)
    print(f"Health: {health}")

    account_fields = [
        "index",
        "username",
        "password",
        "nickname",
        "user_id",
        "interest_domains",
        "profile_summary",
        "scene_hint",
        "profile_source",
        "status",
        "error",
    ]
    question_fields = [
        "username",
        "user_id",
        "question_no",
        "question_id",
        "category_id",
        "interest_domain",
        "title",
        "status",
        "answer_count",
        "error",
    ]

    def write_csv(path: Path, fieldnames: list[str], row: dict[str, Any]) -> None:
        with csv_lock:
            append_csv(path, fieldnames, row)

    def log(message: str, *, error: bool = False) -> None:
        with print_lock:
            print(message, file=sys.stderr if error else sys.stdout, flush=True)

    def process_user(user: DemoUser) -> None:
        profile = profiles[user.username]
        try:
            register_or_login(args.base_url, user)
            write_csv(
                accounts_path,
                account_fields,
                {
                    "index": user.index,
                    "username": user.username,
                    "password": user.password,
                    "nickname": user.nickname,
                    "user_id": user.user_id,
                    "interest_domains": "|".join(profile.interest_domains),
                    "profile_summary": profile.profile_summary,
                    "scene_hint": profile.scene_hint,
                    "profile_source": profile.source,
                    "status": "OK",
                    "error": "",
                },
            )
            log(
                f"[USER OK] {user.index:03d} {user.username} user_id={user.user_id} "
                f"profile={profile.source}"
            )
        except Exception as exc:  # noqa: BLE001 - batch seeding must continue.
            write_csv(
                accounts_path,
                account_fields,
                {
                    "index": user.index,
                    "username": user.username,
                    "password": user.password,
                    "nickname": user.nickname,
                    "user_id": "",
                    "interest_domains": "|".join(profile.interest_domains),
                    "profile_summary": profile.profile_summary,
                    "scene_hint": profile.scene_hint,
                    "profile_source": profile.source,
                    "status": "ERROR",
                    "error": str(exc),
                },
            )
            log(f"[USER ERROR] {user.username}: {exc}", error=True)
            return

        for question_index in range(1, args.questions_per_user + 1):
            question = build_question(user, profile, question_index, categories)
            try:
                response = request_json(
                    args.base_url,
                    "POST",
                    "/api/questions/ask",
                    question,
                    token=user.token,
                    timeout=args.ai_timeout,
                )
                write_csv(
                    questions_path,
                    question_fields,
                    {
                        "username": user.username,
                        "user_id": user.user_id,
                        "question_no": question_index,
                        "question_id": response.get("question_id", ""),
                        "category_id": question["category_id"],
                        "interest_domain": question["interest_domain"],
                        "title": question["title"],
                        "status": response.get("status", "OK"),
                        "answer_count": len(response.get("answers", [])),
                        "error": "",
                    },
                )
                log(
                    f"[ASK OK] {user.username} #{question_index:02d} "
                    f"question_id={response.get('question_id')}"
                )
            except Exception as exc:  # noqa: BLE001 - batch seeding must continue.
                write_csv(
                    questions_path,
                    question_fields,
                    {
                        "username": user.username,
                        "user_id": user.user_id,
                        "question_no": question_index,
                        "question_id": "",
                        "category_id": question["category_id"],
                        "interest_domain": question["interest_domain"],
                        "title": question["title"],
                        "status": "ERROR",
                        "answer_count": "",
                        "error": str(exc),
                    },
                )
                log(f"[ASK ERROR] {user.username} #{question_index:02d}: {exc}", error=True)

            sleep_seconds = random.uniform(args.min_delay, args.max_delay)
            time.sleep(sleep_seconds)

    if args.concurrency == 1:
        for user in users:
            process_user(user)
    else:
        with ThreadPoolExecutor(max_workers=args.concurrency) as executor:
            futures = [executor.submit(process_user, user) for user in users]
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as exc:  # noqa: BLE001 - keep the rest of the batch alive.
                    log(f"[WORKER ERROR] {exc}", error=True)

    print("Seed run completed.")
    print(f"Accounts CSV: {accounts_path}")
    print(f"Questions CSV: {questions_path}")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seed public demo users and AI questions.")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--users", type=int, default=100)
    parser.add_argument("--questions-per-user", type=int, default=10)
    parser.add_argument("--username-prefix", default="demoqa")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--concurrency", type=int, default=1)
    parser.add_argument("--min-delay", type=float, default=1.5)
    parser.add_argument("--max-delay", type=float, default=4.0)
    parser.add_argument("--ai-timeout", type=int, default=240)
    parser.add_argument("--profile-batch-size", type=int, default=DEEPSEEK_PROFILE_BATCH_SIZE)
    parser.add_argument("--strict-profile-retries", type=int, default=STRICT_PROFILE_RETRIES)
    parser.add_argument("--local-profiles-only", action="store_true")
    parser.add_argument("--strict-profiles", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if args.users <= 0:
        parser.error("--users must be greater than 0")
    if args.questions_per_user <= 0:
        parser.error("--questions-per-user must be greater than 0")
    if args.concurrency <= 0 or args.concurrency > 10:
        parser.error("--concurrency must be between 1 and 10")
    if args.profile_batch_size <= 0 or args.profile_batch_size > 50:
        parser.error("--profile-batch-size must be between 1 and 50")
    if args.strict_profile_retries < 0 or args.strict_profile_retries > 5:
        parser.error("--strict-profile-retries must be between 0 and 5")
    if args.strict_profiles and args.local_profiles_only:
        parser.error("--strict-profiles cannot be combined with --local-profiles-only")
    if args.min_delay < 0 or args.max_delay < args.min_delay:
        parser.error("--delay range is invalid")
    return args


if __name__ == "__main__":
    raise SystemExit(run(parse_args()))
