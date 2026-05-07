# 项目交接说明

这份文档面向刚接手本项目的协作者，用来快速说明当前代码状态、已验证内容、启动方式、关键业务规则和下一步优先事项。

## 1. 当前推荐分支

当前推荐基于 `main` 分支继续协作：

```text
main
```

当前文档整理前的本地基线提交：

```text
55bec04
```

现在的 `main` 已经整合了采纳答案、收藏、用户中心、管理员、媒体、头像、问题配图、回答配图、标签增强、AI 多轮追问前端和推荐画像相关能力。

保留但不建议直接合并的安全备份分支：

```text
integrate-collab-updates
backup-local-before-collab-integration
```

它们用于追溯整合过程和本地备份，不是当前推荐交付分支。

## 2. 已验证状态

历史本地验证曾覆盖：

- Docker Desktop 已启动
- `oracle26ai` 容器状态为 `healthy`
- `scripts/validate-oracle-schema.ps1` 已完整通过
- Oracle 对象无编译错误
- 触发器统计校验通过
- 推荐过程幂等性校验通过
- 增强推荐包体已在本地 Oracle 编译为 `VALID`
- 增强推荐冒烟测试已覆盖画像重建、推荐生成、自有问题过滤、已收藏过滤和非 `OPEN` 问题过滤
- 采纳答案跨问题引用已被数据库约束拒绝
- Python 源码编译检查通过
- `app.main` 和 `frontend_cli.main` 导入通过
- CLI `questions` 命令已包含 `accept` 和图片相关命令
- 2026-05-07 分类筛选链路已重新验证：`/api/categories` 仅返回启用分类，`/api/questions`、`/api/search/questions` 和推荐结果均按启用分类口径返回
- 2026-05-07 本地数据库已用真实 DeepSeek API 对历史停用分类问题完成批量重分类，原 `公网快照标签治理` 下 60 条问题已迁入标准启用分类
- 2026-05-07 验证结果：非 `DELETED` 问题不存在停用分类残留，首页问题总数恢复为 81 条，分类筛选与“全部问题”口径一致

推荐重新验证命令：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\validate-oracle-schema.ps1
python -B -c "import app.main; import frontend_cli.main; print('imports ok')"
python -B -m frontend_cli.main questions --help
python .\scripts\reclassify_question_categories.py --scope inactive --limit 5
```

## 3. 环境启动顺序

第一次接手建议按顺序执行：

```powershell
Copy-Item .env.example .env
.\scripts\start-oracle26ai.ps1
.\scripts\load-oracle-schema.ps1
.\scripts\load-seed-data.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\validate-oracle-schema.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API 启动后检查：

- `http://127.0.0.1:8000/`
- `http://127.0.0.1:8000/health`
- `http://127.0.0.1:8000/docs`
- `http://127.0.0.1:8000/login`
- `http://127.0.0.1:8000/home`
- `http://127.0.0.1:8000/home?section=recommend`
- `http://127.0.0.1:8000/home?section=hot`
- `http://127.0.0.1:8000/me`
- `http://127.0.0.1:8000/admin`

## 4. 当前核心能力

已经具备的主链路：

- 用户注册和登录
- JWT 鉴权
- 产品介绍首页
- 纯社区发帖
- AI 首答提问
- 发帖分类、AI 自动分类、已有标签、自定义标签、标签建议和 AI 自动标签
- 人工回答
- 采纳答案
- 问题收藏
- 回答点赞、点踩和评分
- 回答评论和楼中楼回复
- AI 首答多轮追问网页交互
- 搜索和搜索历史
- 推荐 / 热榜首页分区
- 浏览历史
- 用户中心
- 用户画像和推荐
- 管理员用户、分类、标签、问题、评论和日志治理接口
- 用户头像
- 问题配图
- 回答配图

当前网页入口：

- `/`
- `/login`
- `/home`
- `/home?section=recommend`
- `/home?section=hot`
- `/questions/{question_id}`
- `/me`
- `/admin`

当前 CLI 入口：

```powershell
python .\scripts\start_business_test.py
python -m frontend_cli.main menu
```

## 5. 关键业务规则

协作者改代码前必须统一以下口径：

- `POST /api/questions/ask` 会触发 AI 首答。
- `POST /api/questions` 是纯社区发帖，不触发 AI。
- 受保护写接口以 JWT 登录态为主。
- 仍保留的 `user_id` 字段属于过渡兼容字段，必须与当前登录用户一致。
- `MANUAL` 回答必须有真实用户。
- `AI` 和 `SYSTEM` 回答不绑定普通用户。
- 采纳答案只能由提问者或管理员执行。
- 采纳答案后问题状态变为 `RESOLVED`。
- 数据库复合外键保证被采纳回答必须属于当前问题。
- 已采纳问题当前不再接受新人工回答。
- 评论挂在回答下，不直接挂在问题下。
- 评论允许自回复。
- 评论不支持编辑。
- 评论删除是软删除，不级联删除子回复。
- 图片元数据统一保存在 `MEDIA_ASSETS`。
- 统计字段优先由数据库触发器维护，不应在 Python 里重复加减。
- 推荐逻辑优先调用数据库包 `qa_app_pkg`，不要在 Python 服务层复制一套推荐算法。
- 当前推荐 API 入参和出参保持不变，画像和推荐评分增强集中在数据库包体内部。
- 公共分类列表只展示 `ACTIVE` 分类。
- 公共问题列表、搜索结果和推荐结果也必须只返回启用分类下的问题，避免停用分类出现在首页但无法被筛选。
- 历史停用分类问题不应直接隐藏或删除，优先使用 `scripts/reclassify_question_categories.py` 迁移到标准启用分类。

## 6. 数据库交接重点

主 DDL：

```text
sql/create_tables.sql
sql/procedures.sql
sql/triggers.sql
sql/views.sql
sql/seed_data.sql
```

本次整合新增或重点调整：

```text
sql/migrations/20260405_add_answers_user_id.sql
sql/migrations/20260405_add_answer_comments.sql
sql/migrations/20260422_add_media_assets.sql
sql/migrations/20260422_add_question_acceptance.sql
sql/migrations/20260425_extend_chat_session_for_follow_up.sql
sql/migrations/20260427_extend_tag_metadata.sql
sql/migrations/20260429_add_deleted_question_status.sql
sql/migrations/20260429_limit_media_asset_file_size.sql
sql/migrations/20260502_improve_recommendation_scoring.sql
sql/migrations/20260503_refresh_reporting_views.sql
sql/migrations/20260507_standardize_question_categories.sql
```

推荐增强迁移 `20260502_improve_recommendation_scoring.sql` 只替换 `qa_app_pkg` 包体，不修改表结构和现有 API。当前推荐分数由画像分、相似兴趣分、热度分、新鲜度分、已读惩罚、负反馈惩罚和多样性惩罚共同组成。

视图刷新迁移 `20260503_refresh_reporting_views.sql` 用于把报表和展示视图落到已有数据库中，覆盖问题概览、热榜、标签明细、用户行为汇总、媒体明细和 AI 追问会话汇总等查询口径。

分类标准化迁移 `20260507_standardize_question_categories.sql` 用于把历史 `oracle`、`ai` 演示分类收敛到通用问答社区分类，并补齐技术开发、人工智能、学习教育、职场发展、生活方式、健康运动、旅行户外、美食烹饪、家居数码、财经理财、文化娱乐、创作设计和其他问题等标准分类。

历史问题 AI 重分类脚本：

```powershell
# 只预览停用/缺失分类的问题，不写库
python .\scripts\reclassify_question_categories.py --scope inactive --limit 10

# 调用真实 DeepSeek API 并写回本地数据库
python .\scripts\reclassify_question_categories.py --scope inactive --apply
```

脚本默认 dry-run，只有加 `--apply` 才会更新 `QUESTIONS.CATEGORY_ID`。建议先处理 `--scope inactive`，不要轻易对全部问题使用 `--scope all`，除非明确需要重新校准所有历史分类。

采纳答案相关约束要点：

- `questions.accepted_answer_id` 保存当前被采纳回答。
- `answers` 上有 `UNIQUE (question_id, answer_id)`。
- `questions(question_id, accepted_answer_id)` 复合外键引用 `answers(question_id, answer_id)`。
- 这样可以避免“问题 A 采纳问题 B 的答案”。

媒体相关表：

- `MEDIA_ASSETS` 统一保存头像、问题配图、回答配图元数据。
- 图片二进制保存在 `MEDIA_ASSETS.FILE_CONTENT BLOB`。
- `PUBLIC_URL` 指向 `/api/media/files/{file_name}`，由后端从 Oracle BLOB 读取返回。

## 7. 代码入口地图

后端路由：

```text
app/api/routes/
```

业务服务：

```text
app/services/
```

数据库访问：

```text
app/repositories/
```

请求响应模型：

```text
app/schemas/
```

网页前端：

```text
app/web/
```

CLI 测试前端：

```text
frontend_cli/
```

## 8. 当前仍需补齐

建议下一阶段优先级：

1. 评论图片和图片审核后台。
2. 推荐规则人工干预入口。
3. 取消采纳或采纳历史。
4. 标签合并、批量审核和标签质量治理。
5. 写接口兼容字段的继续清理。

已经补齐的前端交互：

- 网页端问题配图和回答配图上传入口已接入，并在详情页正文下方展示。
- 网页端 AI 首答多轮追问入口已接入详情页，支持会话列表、消息展示和创建 / 续写追问。
- 管理员网页后台已接入 `/admin`，覆盖总览、用户治理、分类管理、标签治理、内容治理、登录日志和操作日志。
- 管理员后台已统一为社区蓝色视觉风格，角色、状态和日志类型显示为中文友好文案。
- 内容治理页已经支持从最近问题定位问题 ID、展开回答查看评论 ID，并一键填入治理表单。

## 9. 提交前检查

每次提交前至少做：

```powershell
git status --short
python -B -c "import pathlib; files=list(pathlib.Path('app').rglob('*.py'))+list(pathlib.Path('frontend_cli').rglob('*.py')); [compile(p.read_text(encoding='utf-8'), str(p), 'exec') for p in files]; print(f'compiled {len(files)} files without pycache')"
python -B -c "import app.main; import frontend_cli.main; print('imports ok')"
git diff --check
```

如果改了数据库结构，必须额外执行：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\validate-oracle-schema.ps1
```

不要提交：

- `.env`
- 历史本地 `uploads/` 目录如果存在，只作为旧运行残留，不再是媒体主存储。
- `*.log`
- `__pycache__/`
- 临时测试图片
- 本机绝对路径
- 真实 API Key 或密码
