CANONICAL_CATEGORY_NAMES = [
    "技术开发",
    "人工智能",
    "学习教育",
    "职场发展",
    "生活方式",
    "健康运动",
    "旅行户外",
    "美食烹饪",
    "家居数码",
    "财经理财",
    "文化娱乐",
    "创作设计",
    "其他问题",
]

DEFAULT_CATEGORY_NAME = "其他问题"


def category_order_case_sql(column_name: str = "category_name") -> str:
    cases = [
        f"WHEN {column_name} = '{category_name}' THEN {index * 10}"
        for index, category_name in enumerate(CANONICAL_CATEGORY_NAMES, start=1)
    ]
    return "CASE " + " ".join(cases) + " ELSE 999 END"


def active_category_exists_sql(question_alias: str = "q") -> str:
    return f"""
    EXISTS (
        SELECT 1
        FROM categories c_filter
        WHERE c_filter.category_id = {question_alias}.category_id
          AND c_filter.status = 'ACTIVE'
    )
    """
